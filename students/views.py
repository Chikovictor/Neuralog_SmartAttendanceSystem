import json
from datetime import datetime
from io import BytesIO

import pandas as pd
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from recognition.utils import extract_faces, image_from_bytes, resize_for_speed

from .forms import StudentRegistrationForm
from .models import AttendanceRecord, Student, Unit
from .utils import create_embedding, decode_frames, get_best_face, recognize_student, run_liveness_check


def get_user_role(user):
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "profile", None)
    return profile.user_type if profile else None


def get_units_for_user(user):
    role = get_user_role(user)
    if role == "lecturer":
        return Unit.objects.filter(lecturer=user)
    if role == "manager":
        profile = getattr(user, "profile", None)
        if profile and profile.department:
            return Unit.objects.filter(lecturer__profile__department=profile.department)
        return Unit.objects.none()
    return Unit.objects.all()


def user_can_access_unit(user, unit):
    role = get_user_role(user)
    if role == "admin":
        return True
    if role == "lecturer":
        return unit.lecturer_id == user.id
    if role == "manager":
        profile = getattr(user, "profile", None)
        return bool(profile and profile.department and unit.lecturer.profile.department == profile.department)
    return False


@login_required
def unit_list(request):
    units = get_units_for_user(request.user)
    return render(request, "students/dashboard.html", {"units": units})


@login_required
def unit_detail(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if not user_can_access_unit(request.user, unit):
        return HttpResponseForbidden("You do not have access to this unit.")
    return render(request, "students/unit_detail.html", {"unit": unit})


@login_required
def register_student(request):
    role = get_user_role(request.user)
    if role not in ("admin", "lecturer", "manager"):
        return HttpResponseForbidden("You do not have permission to register students.")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)
        form.fields["units"].queryset = get_units_for_user(request.user)
        if form.is_valid():
            student = form.save(commit=False)

            embeddings = []
            all_uploads = list(form.cleaned_data.get("face_images", []))
            max_images = getattr(settings, "MAX_FACE_IMAGES", 8)
            uploads = all_uploads
            truncated = False
            if max_images and len(all_uploads) > max_images:
                uploads = all_uploads[:max_images]
                truncated = True
            processed = 0
            for upload in uploads:
                processed += 1
                image = image_from_bytes(upload.read())
                if image is None:
                    continue
                image = resize_for_speed(image)
                faces = extract_faces(image, max_faces=1)
                if not faces:
                    continue
                emb = create_embedding(faces[0])
                embeddings.append(emb.tolist())

            if not embeddings:
                message = "No faces detected in the uploaded images. Please try clearer photos."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"message": message}, status=400)
                messages.error(request, message)
                return redirect("students:register_student")

            student.face_encodings = embeddings
            student.save()
            student.units.set(form.cleaned_data.get("units"))

            message = f"Student {student.full_name} registered. Processed {processed}/{len(uploads)} images."
            if truncated:
                message += f" (Using first {max_images} images for speed.)"

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "message": message,
                        "processed": processed,
                        "total": len(uploads),
                        "embeddings": len(embeddings),
                    }
                )

            messages.success(request, message)
            return redirect("students:unit_list")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"message": "Please correct the highlighted errors."}, status=400)
    else:
        form = StudentRegistrationForm()
        form.fields["units"].queryset = get_units_for_user(request.user)

    return render(request, "students/register_student.html", {"form": form})


@login_required
def take_attendance(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if not user_can_access_unit(request.user, unit):
        return HttpResponseForbidden("You do not have access to this unit.")
    return render(
        request,
        "students/take_attendance.html",
        {
            "unit": unit,
            "frame_count": getattr(settings, "ATTENDANCE_FRAME_COUNT", 6),
            "frame_delay": getattr(settings, "ATTENDANCE_FRAME_DELAY_MS", 120),
        },
    )


@login_required
def take_attendance_submit(request, unit_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=400)

    unit = get_object_or_404(Unit, id=unit_id)
    if not user_can_access_unit(request.user, unit):
        return JsonResponse({"error": "Access denied."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    frames = decode_frames(payload)
    if not frames:
        return JsonResponse({"error": "No frames received."}, status=400)

    warning = None
    skip_liveness = payload.get("skip_liveness")
    if getattr(settings, "LIVENESS_REQUIRED", True) and not skip_liveness:
        liveness_ok, liveness_warning = run_liveness_check(frames)
        if liveness_ok is False:
            return JsonResponse(
                {"error": "Liveness check failed - please look at the camera and blink naturally."},
                status=400,
            )
        if liveness_warning:
            warning = liveness_warning

    best_face, face_count = get_best_face(frames)
    if face_count > 1:
        return JsonResponse({"error": "Multiple faces detected. Please ensure only one face is visible."}, status=400)
    if best_face is None:
        return JsonResponse({"error": "No face detected. Please try again."}, status=400)

    embedding = create_embedding(best_face)
    threshold = getattr(settings, "FACE_MATCH_THRESHOLD", 0.65)
    student, confidence_pct, _distance = recognize_student(embedding, unit.students.all(), threshold)

    if not student:
        register_url = reverse("students:register_student")
        return JsonResponse(
            {
                "error": "Unknown face - not enrolled in this unit.",
                "register_url": register_url,
                "confidence": confidence_pct,
            },
            status=400,
        )

    today = timezone.localdate()
    record, created = AttendanceRecord.objects.get_or_create(
        student=student,
        unit=unit,
        date=today,
        defaults={"timestamp": timezone.now(), "confidence": confidence_pct, "status": "present"},
    )
    if created:
        message = f"Marked present: {student.full_name} ({confidence_pct}% confidence) for {unit.code}."
    else:
        message = f"Already marked present today at {record.timestamp.strftime('%H:%M')}."

    response = {
        "message": message,
        "student": student.full_name,
        "unit": unit.code,
        "confidence": confidence_pct,
        "already_marked": not created,
    }
    if warning:
        response["warning"] = warning
    return JsonResponse(response)


@login_required
def attendance_report(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if not user_can_access_unit(request.user, unit):
        return HttpResponseForbidden("You do not have access to this report.")

    records = AttendanceRecord.objects.filter(unit=unit).select_related("student")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    student_query = request.GET.get("student")

    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if student_query:
        records = records.filter(
            Q(student__student_id__icontains=student_query)
            | Q(student__first_name__icontains=student_query)
            | Q(student__last_name__icontains=student_query)
        )

    export = request.GET.get("export")
    report_rows = []

    if date_from and date_to and date_from == date_to:
        target_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        present_map = {rec.student_id: rec for rec in records.filter(date=target_date)}
        for student in unit.students.all():
            rec = present_map.get(student.id)
            if rec:
                report_rows.append(rec)
            else:
                report_rows.append(
                    AttendanceRecord(
                        student=student,
                        unit=unit,
                        date=target_date,
                        timestamp=timezone.make_aware(datetime.combine(target_date, datetime.min.time())),
                        confidence=0.0,
                        status="absent",
                    )
                )
    else:
        report_rows = list(records)

    if export in ("csv", "xlsx"):
        data = []
        for rec in report_rows:
            data.append(
                {
                    "Student ID": rec.student.student_id,
                    "Name": rec.student.full_name,
                    "Unit": unit.code,
                    "Date": rec.date,
                    "Time": rec.timestamp.strftime("%H:%M"),
                    "Confidence": rec.confidence,
                    "Status": rec.status,
                }
            )
        df = pd.DataFrame(data)
        if export == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{unit.code}_attendance.csv"'
            df.to_csv(response, index=False)
            return response

        output = BytesIO()
        df.to_excel(output, index=False)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{unit.code}_attendance.xlsx"'
        return response

    return render(
        request,
        "students/attendance_report.html",
        {
            "unit": unit,
            "records": report_rows,
            "date_from": date_from,
            "date_to": date_to,
            "student_query": student_query,
        },
    )
