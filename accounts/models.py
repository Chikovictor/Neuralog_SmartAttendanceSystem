from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    USER_TYPES = (
        ("admin", "System Administrator"),
        ("lecturer", "Lecturer"),
        ("manager", "Manager/HOD"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default="lecturer")
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.user_type})"
