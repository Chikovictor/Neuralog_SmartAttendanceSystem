from django import forms

from accounts.fields import MultiFileInput, MultiImageField

from .models import Student


class StudentRegistrationForm(forms.ModelForm):
    face_images = MultiImageField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
        help_text="Upload at least 5 clear face images.",
    )
    class Meta:
        model = Student
        fields = ("student_id", "full_name", "email", "face_images")

    def clean_face_images(self):
        images = self.cleaned_data.get("face_images", [])
        if images and len(images) < 5:
            raise forms.ValidationError("Please upload at least 5 images.")
        return images
