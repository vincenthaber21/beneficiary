"""Keep linked beneficiary personal fields in sync with the citizen registry."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Citizen


@receiver(post_save, sender=Citizen)
def sync_linked_beneficiary(sender, instance, **kwargs):
    beneficiary = getattr(instance, "beneficiary", None)
    if beneficiary is None:
        return
    # Avoid recursive saves if nothing changed.
    before = (
        beneficiary.last_name,
        beneficiary.first_name,
        beneficiary.middle_name,
        beneficiary.sex,
        beneficiary.contact_number,
        beneficiary.address,
        beneficiary.barangay,
        beneficiary.municipality,
        beneficiary.province,
        beneficiary.rfid_id,
        beneficiary.signature,
        beneficiary.beneficiary_class,
        beneficiary.monthly_income,
    )
    beneficiary.sync_from_citizen(instance)
    after = (
        beneficiary.last_name,
        beneficiary.first_name,
        beneficiary.middle_name,
        beneficiary.sex,
        beneficiary.contact_number,
        beneficiary.address,
        beneficiary.barangay,
        beneficiary.municipality,
        beneficiary.province,
        beneficiary.rfid_id,
        beneficiary.signature,
        beneficiary.beneficiary_class,
        beneficiary.monthly_income,
    )
    if before != after:
        beneficiary.save(update_fields=[
            "last_name", "first_name", "middle_name", "sex",
            "contact_number", "address", "barangay", "municipality", "province",
            "rfid_id", "signature", "beneficiary_class", "monthly_income",
        ])
