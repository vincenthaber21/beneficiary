from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_mgmt", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "System Administrator"),
                    ("staff", "Staff"),
                    ("distributor", "Ayuda Distributor"),
                ],
                default="staff",
                max_length=20,
            ),
        ),
    ]
