from django.urls import path

from . import views

urlpatterns = [
    path("webcam/", views.webcam_page, name="webcam_page"),
    path("webcam/submit/", views.webcam_attendance, name="webcam_attendance"),
]
