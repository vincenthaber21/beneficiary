from django.db import migrations, models


VULNERABLE_GROUPS = [
    ("senior", "Senior Citizen"),
    ("pwd", "Person with Disability (PWD)"),
    ("solo_parent", "Solo Parent"),
    ("indigent", "Indigent"),
    ("pregnant", "Pregnant"),
    ("lactating", "Lactating Mother"),
    ("ip", "Indigenous People"),
    ("farmer", "Tobacco Farmer"),
    ("fisherfolk", "Fisherfolk"),
    ("youth", "Youth"),
    ("4ps", "4Ps Beneficiary"),
]

HEALTH_CONDITIONS = [
    ("chronic", "Chronic Illness"),
    ("mental", "Mental Disability"),
    ("physical", "Physical Disability"),
    ("visual", "Visual Impairment"),
    ("hearing", "Hearing Impairment"),
    ("speech", "Speech Impairment"),
    ("diabetes", "Diabetes"),
    ("hypertension", "Hypertension"),
    ("cancer", "Cancer"),
    ("other", "Other"),
]


def seed_catalogs(apps, schema_editor):
    VulnerableGroup = apps.get_model("citizens", "VulnerableGroup")
    HealthCondition = apps.get_model("citizens", "HealthCondition")
    for index, (code, name) in enumerate(VULNERABLE_GROUPS):
        VulnerableGroup.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True, "sort_order": index},
        )
    for index, (code, name) in enumerate(HEALTH_CONDITIONS):
        HealthCondition.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True, "sort_order": index},
        )


def unseed_catalogs(apps, schema_editor):
    VulnerableGroup = apps.get_model("citizens", "VulnerableGroup")
    HealthCondition = apps.get_model("citizens", "HealthCondition")
    VulnerableGroup.objects.filter(code__in=[code for code, _name in VULNERABLE_GROUPS]).delete()
    HealthCondition.objects.filter(code__in=[code for code, _name in HEALTH_CONDITIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("citizens", "0009_civil_status_live_in"),
    ]

    operations = [
        migrations.CreateModel(
            name="VulnerableGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Vulnerable Group",
                "verbose_name_plural": "Vulnerable Groups",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="HealthCondition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Health Condition",
                "verbose_name_plural": "Health Conditions",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.RunPython(seed_catalogs, unseed_catalogs),
    ]
