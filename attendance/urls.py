from django.urls import path

from . import views

urlpatterns = [
    path("students/register/", views.register_student, name="student_register"),
]
