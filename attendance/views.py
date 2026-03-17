from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from recognition.utils import extract_faces, get_embedding, image_from_bytes

from .forms import StudentRegistrationForm
from .models import Student


def get_user_role(user):
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "profile", None)
    return profile.user_type if profile else None


@login_required
def register_student(request):
    role = get_user_role(request.user)
    if role not in ("admin", "lecturer", "manager"):
        return HttpResponseForbidden("You do not have permission to register students.")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.save()

            embeddings = []
            uploads = form.cleaned_data.get("face_images", [])
            for upload in uploads:
                image = image_from_bytes(upload.read())
                if image is None:
                    continue
                faces = extract_faces(image, max_faces=1)
                for face in faces:
                    emb = get_embedding(face)
                    embeddings.append(emb.tolist())

            if not embeddings:
                messages.warning(request, "No faces detected in uploads. You can add them later.")
            student.face_encodings = embeddings
            student.save(update_fields=["face_encodings"])
            messages.success(request, f"Student {student.full_name} registered.")
            return redirect("dashboard")
    else:
        form = StudentRegistrationForm()

    return render(request, "attendance/student_register.html", {"form": form})
