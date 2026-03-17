from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import StaffRegistrationForm


def get_user_role(user):
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "profile", None)
    return profile.user_type if profile else None


def home(request):
    if request.user.is_authenticated:
        return redirect("students:unit_list")
    return redirect("login")


@login_required
def register_staff(request):
    role = get_user_role(request.user)
    if role != "admin":
        return HttpResponseForbidden("Only admins can register staff.")

    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.user_type = form.cleaned_data.get("user_type")
            profile.employee_id = form.cleaned_data.get("employee_id")
            profile.department = form.cleaned_data.get("department")
            profile.save()
            messages.success(request, "Staff account created.")
            return redirect("students:unit_list")
    else:
        form = StaffRegistrationForm()

    return render(request, "accounts/register_staff.html", {"form": form})
