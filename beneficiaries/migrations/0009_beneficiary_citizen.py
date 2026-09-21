import django.db.models.deletion
from django.db import migrations, models


def _income_from_range(income_range):
    """Map citizen income_range choice to a numeric monthly_income default."""
    mapping = {
        "0-15000": 7500,
        "15001-30000": 22500,
        "30001-50000": 40000,
        "50001-80000": 65000,
        "80001+": 80001,
    }
    return mapping.get(income_range or "", 0)


def _class_from_vulnerable(groups):
    """Pick a beneficiary class from citizen vulnerable_groups when possible."""
    mapping = {
        "solo_parent": "Solo Parent",
        "pwd": "PWD",
        "senior": "Senior Citizen",
        "lactating": "Lactating Mother",
        "farmer": "Rice Farmer",
    }
    for g in groups or []:
        if g in mapping:
            return mapping[g]
    return "PWD"  # safe default for eligibility form; staff can edit


def link_beneficiaries_to_citizens(apps, schema_editor):
    Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
    Citizen = apps.get_model("citizens", "Citizen")

    # Index existing citizens by normalized name for matching.
    by_name = {}
    for c in Citizen.objects.all():
        key = (
            (c.last_name or "").strip().lower(),
            (c.first_name or "").strip().lower(),
            (c.middle_name or "").strip().lower(),
        )
        by_name.setdefault(key, c)

    used_citizen_ids = set()

    for b in Beneficiary.objects.all().order_by("pk"):
        if b.citizen_id:
            used_citizen_ids.add(b.citizen_id)
            continue

        key = (
            (b.last_name or "").strip().lower(),
            (b.first_name or "").strip().lower(),
            (b.middle_name or "").strip().lower(),
        )
        citizen = by_name.get(key)

        # Also try matching without middle name if exact key missed.
        if citizen is None or citizen.pk in used_citizen_ids:
            citizen = None
            for (ln, fn, _mn), c in by_name.items():
                if c.pk in used_citizen_ids:
                    continue
                if ln == key[0] and fn == key[1]:
                    citizen = c
                    break

        if citizen is None:
            citizen = Citizen.objects.create(
                last_name=b.last_name,
                first_name=b.first_name,
                middle_name=b.middle_name or "",
                sex=b.sex or "",
                contact_number=b.contact_number or "",
                address=(b.address or "")[:255],
                barangay=b.barangay or "",
                municipality=b.municipality or "Bacnotan",
                province=b.province or "La Union",
                rfid_tag=b.rfid_id or "",
                signature=b.signature or "",
                status="active" if b.is_active else "inactive",
                notes=b.notes or "",
            )
            # Mirror auto registry_no assignment used by the live Citizen.save().
            if not citizen.registry_no:
                year = (b.date_registered.year if b.date_registered else 2026)
                candidate = f"CR-{year}-{citizen.pk:05d}"
                suffix = 0
                base = candidate
                while Citizen.objects.filter(registry_no=candidate).exclude(pk=citizen.pk).exists():
                    suffix += 1
                    candidate = f"{base}-{suffix}"
                citizen.registry_no = candidate
                citizen.save(update_fields=["registry_no"])
            by_name[key] = citizen

        used_citizen_ids.add(citizen.pk)
        b.citizen_id = citizen.pk
        # Keep beneficiary personal cache aligned with linked citizen.
        b.last_name = citizen.last_name
        b.first_name = citizen.first_name
        b.middle_name = citizen.middle_name or ""
        b.sex = citizen.sex or b.sex or ""
        b.contact_number = citizen.contact_number or b.contact_number or ""
        b.address = citizen.address or b.address or ""
        b.barangay = citizen.barangay or b.barangay or ""
        b.municipality = citizen.municipality or b.municipality or ""
        b.province = citizen.province or b.province or ""
        if citizen.rfid_tag and not b.rfid_id:
            b.rfid_id = citizen.rfid_tag
        if citizen.signature and not b.signature:
            b.signature = citizen.signature
        b.save(update_fields=[
            "citizen_id", "last_name", "first_name", "middle_name", "sex",
            "contact_number", "address", "barangay", "municipality", "province",
            "rfid_id", "signature",
        ])


def unlink_beneficiaries(apps, schema_editor):
    Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
    Beneficiary.objects.update(citizen_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("citizens", "0008_uniq_fingerprint_template"),
        ("beneficiaries", "0008_uniq_fingerprint_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="beneficiary",
            name="citizen",
            field=models.OneToOneField(
                blank=True,
                help_text="Linked citizen registry record. One citizen may only be enrolled once.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="beneficiary",
                to="citizens.citizen",
                verbose_name="Citizen",
            ),
        ),
        migrations.RunPython(link_beneficiaries_to_citizens, unlink_beneficiaries),
    ]
