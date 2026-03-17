from django.contrib import admin

from .models import AttendanceRecord, Student, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "lecturer")
    search_fields = ("code", "name")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "first_name", "last_name", "email")
    search_fields = ("student_id", "first_name", "last_name")
    filter_horizontal = ("units",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "unit", "date", "timestamp", "confidence", "status")
    list_filter = ("unit", "date")
