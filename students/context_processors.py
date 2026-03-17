from .models import Unit


def get_user_role(user):
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "profile", None)
    return profile.user_type if profile else None


def nav_units(request):
    if not request.user.is_authenticated:
        return {}

    role = get_user_role(request.user)
    if role == "lecturer":
        units = Unit.objects.filter(lecturer=request.user)
    elif role == "manager":
        profile = getattr(request.user, "profile", None)
        if profile and profile.department:
            units = Unit.objects.filter(lecturer__profile__department=profile.department)
        else:
            units = Unit.objects.none()
    else:
        units = Unit.objects.all()

    return {"nav_units": units}
