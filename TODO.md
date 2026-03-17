# NeuraLog Registration Fixes TODO

## Approved Plan Steps:

- [x] 1. Update `students/models.py`: Add verbose_name="Registration No.", max_length=25, RegexValidator for student_id format ^[A-Z]{2}\\d{2}/\\d{5,6}/\\d{2}$.
- [x] 2. Update `students/forms.py`: Add labels={"student_id": "Registration No."}, adjust clean_face_images min to 3.
- [x] 3. Update `students/views.py`: Enhance register_student error handling to return form.errors in JSON for AJAX.
- [x] 4. Update `students/templates/students/register_student.html`: Improve JS to display specific form errors.
- [x] 5. Run migrations: `python manage.py makemigrations students && python manage.py migrate`
  (Done)
- [x] 6. Test registration with sample data (IN13/00159/23, 5+ images).
- [x] 7. (Optional) Update accounts/forms.py labels.
**All steps complete!**

Progress will be updated after each step.
