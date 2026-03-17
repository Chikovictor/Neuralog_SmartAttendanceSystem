from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="employee_id",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name="profile",
            name="department",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="profile",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("admin", "System Administrator"),
                    ("lecturer", "Lecturer"),
                    ("manager", "Manager/HOD"),
                ],
                default="lecturer",
                max_length=10,
            ),
        ),
    ]
