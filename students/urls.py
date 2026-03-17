from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.unit_list, name="unit_list"),
    path("units/<int:unit_id>/", views.unit_detail, name="unit_detail"),
    path("units/<int:unit_id>/attendance/", views.take_attendance, name="take_attendance"),
    path("units/<int:unit_id>/attendance/submit/", views.take_attendance_submit, name="take_attendance_submit"),
    path("units/<int:unit_id>/reports/", views.attendance_report, name="attendance_report"),
    path("register/", views.register_student, name="register_student"),
]
