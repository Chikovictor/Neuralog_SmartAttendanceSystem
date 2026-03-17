from django.db import models
from django.utils import timezone


class Student(models.Model):
    student_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    face_encodings = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.student_id})"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ("present", "Present"),
        ("late", "Late"),
        ("absent", "Absent"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="present")

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date", "-timestamp"]

    def __str__(self) -> str:
        return f"{self.student.full_name} ({self.date})"
