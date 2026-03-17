import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from students.models import AttendanceRecord, Student
from recognition.utils import (
    detect_blink_from_frames,
    get_embedding,
    image_from_base64,
    match_student_embedding,
    select_best_face_from_frames,
)


@login_required
@ensure_csrf_cookie
def webcam_page(request):
    return render(request, "recognition/webcam.html")


@login_required
def webcam_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    frames_b64 = payload.get("frames", [])
    if not frames_b64:
        return JsonResponse({"error": "No frames provided."}, status=400)

    frames = []
    for frame_data in frames_b64:
        frame = image_from_base64(frame_data)
        if frame is not None:
            frames.append(frame)

    if not frames:
        return JsonResponse({"error": "Unable to decode frames."}, status=400)

    warning = None
    blink_ok = detect_blink_from_frames(frames)
    if blink_ok is None:
        warning = "MediaPipe not installed; proceeding without liveness check."
    elif not blink_ok:
        return JsonResponse({"error": "Blink not detected. Please try again."}, status=400)

    best_face, face_count = select_best_face_from_frames(frames)
    if face_count > 1:
        return JsonResponse({"error": "Multiple faces detected. Please use one face only."}, status=400)
    if best_face is None:
        return JsonResponse({"error": "No face detected."}, status=400)

    emb = get_embedding(best_face)
    students = Student.objects.all()
    student, confidence, _distance = match_student_embedding(emb, students, threshold=0.6)
    confidence_pct = round(confidence * 100, 2)
    if not student:
        return JsonResponse(
            {"error": "New face - please register first.", "confidence": confidence_pct},
            status=400,
        )

    today = timezone.localdate()
    record, created = AttendanceRecord.objects.get_or_create(
        student=student,
        date=today,
        defaults={"status": "present", "timestamp": timezone.now()},
    )

    display_name = getattr(student, "name", None) or getattr(student, "full_name", "")
    if created:
        message = f"Marked present: {display_name} ({confidence_pct}% confidence)"
    else:
        message = f"Already marked present today: {display_name} ({confidence_pct}% confidence)"

    response = {
        "message": message,
        "student": display_name,
        "date": str(record.date),
        "confidence": confidence_pct,
    }
    if warning:
        response["warning"] = warning
    return JsonResponse(response)
