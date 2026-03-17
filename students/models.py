from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class Unit(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"profile__user_type": "lecturer"},
        related_name="units",
    )

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Student(models.Model):
    student_id = models.CharField(
        max_length=25,
        verbose_name="Registration No.",
        validators=[
            RegexValidator(
                r"^[A-Z]{2}\d{2}/\d{5,6}/\d{2}$",
                "Enter valid Registration No. (e.g. IN13/00159/23)"
            )
        ],
        unique=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    face_encodings = models.JSONField(default=list)
    units = models.ManyToManyField(Unit, related_name="students", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.student_id})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, default="present")

    class Meta:
        unique_together = ("student", "unit", "date")
        ordering = ["-date", "-timestamp"]

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.unit.code} ({self.date})"
