from django import forms

from accounts.fields import MultiFileInput, MultiImageField

from .models import Student, Unit


class StudentRegistrationForm(forms.ModelForm):
    face_images = MultiImageField(
        required=True,
        widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"}),
        help_text="Upload at least 5 clear face images.",
    )
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        required=False,
    )

    class Meta:
        model = Student
        fields = ("student_id", "first_name", "last_name", "email", "units", "face_images")
        widgets = {
            "student_id": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_face_images(self):
        images = self.cleaned_data.get("face_images", [])
        if len(images) < 5:
            raise forms.ValidationError("Please upload at least 5 images.")
        return images
