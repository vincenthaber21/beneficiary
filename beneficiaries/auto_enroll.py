"""
Auto-determine / enroll beneficiaries from the Citizen Registry.

A citizen is enrollable when:
  - status is ``active``
  - not already linked to a beneficiary
  - vulnerable groups / occupation map to a valid beneficiary class

Monthly income is copied from the citizen record when available, but is
not used to decide qualification (class + grant cooldown only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from checker.logic import VALID_CLASSES
from citizens.models import Citizen, CitizenFamilyMember

from .forms import invalidate_citizen_enrollment_cache
from .models import Beneficiary, FamilyMember, eligibility_from_citizen


@dataclass
class AutoEnrollResult:
    created: int = 0
    synced: int = 0
    skipped_no_class: int = 0
    skipped_already: int = 0
    family_links: int = 0
    total_enrollable: int = 0
    created_names: list = field(default_factory=list)
    preview: list = field(default_factory=list)

    @property
    def enrollable_count(self):
        return self.total_enrollable or len(self.preview)


def assess_citizen(citizen, *, qualified_only=True):
    """Return (ok, reason, ben_class, monthly) for one citizen.

    ``qualified_only`` is kept for call-site compatibility; income is not
    used for qualification anymore.
    """
    ben_class, monthly = eligibility_from_citizen(citizen)
    if not ben_class or ben_class not in VALID_CLASSES:
        return False, "no_class", ben_class or "", monthly
    return True, "ok", ben_class, monthly


def enrollable_citizens_qs():
    """Active citizens not yet enrolled as beneficiaries."""
    enrolled_ids = (
        Beneficiary.objects.exclude(citizen__isnull=True)
        .values_list("citizen_id", flat=True)
    )
    return (
        Citizen.objects.filter(status="active")
        .exclude(pk__in=enrolled_ids)
        .order_by("last_name", "first_name")
    )


def preview_auto_enroll(*, qualified_only=True, limit=50):
    """Scan citizens and return a dry-run AutoEnrollResult."""
    result = AutoEnrollResult()
    total_enrollable = 0
    for citizen in enrollable_citizens_qs().iterator(chunk_size=500):
        ok, reason, ben_class, monthly = assess_citizen(
            citizen, qualified_only=qualified_only
        )
        if not ok:
            if reason == "no_class":
                result.skipped_no_class += 1
            continue
        total_enrollable += 1
        if limit is None or len(result.preview) < limit:
            result.preview.append({
                "pk": citizen.pk,
                "registry_no": citizen.registry_no or "",
                "name": citizen.full_name,
                "barangay": citizen.barangay or "",
                "beneficiary_class": ben_class,
                "monthly_income": float(monthly) if monthly is not None else None,
                "income_range": citizen.get_income_range_display() or "",
            })
    result.total_enrollable = total_enrollable
    return result


def _create_beneficiary(citizen, ben_class, monthly) -> Beneficiary:
    if monthly is None:
        monthly = Decimal("0.00")
    ben = Beneficiary(
        citizen=citizen,
        beneficiary_class=ben_class,
        monthly_income=monthly,
        is_active=True,
    )
    ben.sync_from_citizen(citizen)
    # Ensure required fields are set even if sync left defaults empty.
    if not ben.beneficiary_class:
        ben.beneficiary_class = ben_class
    if ben.monthly_income is None:
        ben.monthly_income = monthly
    ben.save()
    return ben


def _sync_existing_from_citizens() -> int:
    """Refresh personal cache + class/income on already-linked beneficiaries."""
    synced = 0
    qs = (
        Beneficiary.objects.exclude(citizen__isnull=True)
        .select_related("citizen")
    )
    for ben in qs.iterator(chunk_size=200):
        c = ben.citizen
        if c is None:
            continue
        before = (
            ben.last_name, ben.first_name, ben.middle_name, ben.sex,
            ben.contact_number, ben.address, ben.barangay,
            ben.municipality, ben.province, ben.rfid_id, ben.signature,
            ben.beneficiary_class, ben.monthly_income,
        )
        ben.sync_from_citizen(c)
        after = (
            ben.last_name, ben.first_name, ben.middle_name, ben.sex,
            ben.contact_number, ben.address, ben.barangay,
            ben.municipality, ben.province, ben.rfid_id, ben.signature,
            ben.beneficiary_class, ben.monthly_income,
        )
        if before != after:
            ben.save()
            synced += 1
    return synced


def _link_families_from_citizens() -> int:
    """Create FamilyMember links from CitizenFamilyMember where both sides enrolled."""
    ben_by_citizen = {
        b.citizen_id: b
        for b in Beneficiary.objects.exclude(citizen__isnull=True)
        .only("id", "citizen_id")
    }
    if not ben_by_citizen:
        return 0

    existing = set(
        FamilyMember.objects.exclude(member__isnull=True)
        .values_list("beneficiary_id", "member_id")
    )
    created = 0
    links = (
        CitizenFamilyMember.objects
        .exclude(member__isnull=True)
        .filter(citizen_id__in=ben_by_citizen.keys(), member_id__in=ben_by_citizen.keys())
        .only("citizen_id", "member_id", "relationship")
    )
    for fm in links.iterator(chunk_size=500):
        head = ben_by_citizen.get(fm.citizen_id)
        member = ben_by_citizen.get(fm.member_id)
        if not head or not member or head.pk == member.pk:
            continue
        pair = (head.pk, member.pk)
        if pair in existing:
            continue
        FamilyMember.objects.create(
            beneficiary=head,
            member=member,
            relationship=fm.relationship or "Other",
            age=None,
        )
        existing.add(pair)
        created += 1
    return created


@transaction.atomic
def auto_enroll_from_citizens(*, qualified_only=True, sync_existing=True, link_families=True):
    """
    Enroll all enrollable citizens as beneficiaries.

    Returns an AutoEnrollResult with counts.
    """
    result = AutoEnrollResult()
    result.skipped_already = Beneficiary.objects.exclude(citizen__isnull=True).count()

    for citizen in enrollable_citizens_qs().iterator(chunk_size=200):
        ok, reason, ben_class, monthly = assess_citizen(
            citizen, qualified_only=qualified_only
        )
        if not ok:
            if reason == "no_class":
                result.skipped_no_class += 1
            continue
        ben = _create_beneficiary(citizen, ben_class, monthly)
        result.created += 1
        if len(result.created_names) < 25:
            result.created_names.append(ben.full_name)

    if sync_existing:
        result.synced = _sync_existing_from_citizens()

    if link_families:
        result.family_links = _link_families_from_citizens()

    invalidate_citizen_enrollment_cache()
    return result
