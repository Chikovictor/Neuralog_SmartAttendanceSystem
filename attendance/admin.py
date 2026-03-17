from django.contrib import admin

from .models import AttendanceRecord, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "email")
    search_fields = ("student_id", "full_name", "email")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "timestamp", "status")
    list_filter = ("date", "status")
    search_fields = ("student__student_id", "student__full_name")
