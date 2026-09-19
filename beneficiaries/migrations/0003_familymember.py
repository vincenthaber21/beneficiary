from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('beneficiaries', '0002_add_prior_grant_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='FamilyMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('relationship', models.CharField(
                    choices=[
                        ('Spouse', 'Spouse'),
                        ('Child', 'Child'),
                        ('Parent', 'Parent'),
                        ('Sibling', 'Sibling'),
                        ('Grandparent', 'Grandparent'),
                        ('Grandchild', 'Grandchild'),
                        ('Other', 'Other'),
                    ],
                    max_length=50,
                )),
                ('age', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('beneficiary', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='family_members',
                    to='beneficiaries.beneficiary',
                )),
            ],
            options={
                'ordering': ['relationship', 'full_name'],
            },
        ),
    ]
