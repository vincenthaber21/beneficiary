from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0001_initial"),
        ("beneficiaries", "0010_familymember_citizen"),
    ]

    operations = [
        migrations.AddField(
            model_name="beneficiary",
            name="program",
            field=models.ForeignKey(
                blank=True,
                help_text="The single assistance program this beneficiary may avail.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="enrolled_beneficiaries",
                to="programs.assistanceprogram",
                verbose_name="Assistance Program",
            ),
        ),
    ]
