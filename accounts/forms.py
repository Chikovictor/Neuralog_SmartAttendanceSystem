from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class StaffRegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=Profile.USER_TYPES)
    employee_id = forms.CharField(required=False)
    department = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "user_type",
            "employee_id",
            "department",
        )
