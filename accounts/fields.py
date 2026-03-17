from django import forms
from django.forms import ClearableFileInput


class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultiImageField(forms.ImageField):
    widget = MultiFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            cleaned = []
            for item in data:
                try:
                    cleaned.append(super().clean(item, initial))
                except (ModuleNotFoundError, ImportError) as exc:
                    raise forms.ValidationError(
                        "Image processing requires Pillow. Install with: pip install Pillow"
                    ) from exc
            return cleaned
        try:
            return [super().clean(data, initial)]
        except (ModuleNotFoundError, ImportError) as exc:
            raise forms.ValidationError(
                "Image processing requires Pillow. Install with: pip install Pillow"
            ) from exc
