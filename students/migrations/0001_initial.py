from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Unit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "lecturer",
                    models.ForeignKey(
                        limit_choices_to={"profile__user_type": "lecturer"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="units",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(max_length=20, unique=True)),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("face_encodings", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("units", models.ManyToManyField(blank=True, related_name="students", to="students.unit")),
            ],
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(default=django.utils.timezone.localdate)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("confidence", models.FloatField(default=0.0)),
                ("status", models.CharField(default="present", max_length=10)),
                (
                    "student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="students.student"),
                ),
                ("unit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="students.unit")),
            ],
            options={
                "ordering": ["-date", "-timestamp"],
                "unique_together": {("student", "unit", "date")},
            },
        ),
    ]
