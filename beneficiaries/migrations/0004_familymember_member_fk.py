import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beneficiaries', '0003_familymember'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='familymember',
            name='full_name',
        ),
        migrations.AddField(
            model_name='familymember',
            name='member',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='member_of',
                to='beneficiaries.beneficiary',
                verbose_name='Beneficiary',
            ),
        ),
    ]
