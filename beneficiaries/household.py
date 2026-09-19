"""Household-level grant cooldown.

Business rule: if ONE member of a family has received a released program grant
within the cooldown window, the WHOLE family is not qualified to receive another
program until that cooldown expires.

Families are the connected components of the FamilyMember link graph (links are
bidirectional: A→B also means B→A).
"""
from datetime import timedelta
from django.utils import timezone

from .models import Beneficiary, FamilyMember
from records.models import GrantRecord


def build_family_components():
    """Return a list of families, each a list of beneficiary ids, over ALL
    beneficiaries (connected components of the family-link graph)."""
    ids = list(Beneficiary.objects.values_list("id", flat=True))
    adj = {i: set() for i in ids}
    for a, b in (
        FamilyMember.objects.exclude(member__isnull=True)
        .values_list("beneficiary_id", "member_id")
    ):
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    seen, comps = set(), []
    for i in ids:
        if i in seen:
            continue
        stack, comp = [i], []
        while stack:
            c = stack.pop()
            if c in seen:
                continue
            seen.add(c)
            comp.append(c)
            stack.extend(adj[c] - seen)
        comps.append(comp)
    return comps


def household_cooldown(months=3):
    """Return ``(blocker_id_map, name_map, date_map)``.

    * ``blocker_id_map``  – beneficiary_id → id of a family member who received a
      released grant within the window, for every beneficiary whose HOUSEHOLD is
      in cooldown. Prefers a member OTHER than the beneficiary themselves.
    * ``name_map``  – blocker id → full name (for display).
    * ``date_map``  – blocker id → most recent qualifying ``date_granted``.
    """
    cutoff = timezone.now().date() - timedelta(days=months * 30)

    # Most recent released grant per beneficiary within the window
    recent = {}
    for bid, dg in (
        GrantRecord.objects.filter(status="released", date_granted__gte=cutoff)
        .values_list("beneficiary_id", "date_granted")
    ):
        if bid not in recent or dg > recent[bid]:
            recent[bid] = dg
    in_cooldown = set(recent)

    blocker_id_map = {}
    for comp in build_family_components():
        cds = [i for i in comp if i in in_cooldown]
        if not cds:
            continue
        for m in comp:
            # Prefer a blocker who is NOT the member themselves
            blocker_id_map[m] = next((c for c in cds if c != m), cds[0])

    blocker_ids = set(blocker_id_map.values())
    name_map = {
        b.id: b.full_name for b in Beneficiary.objects.filter(id__in=blocker_ids)
    }
    date_map = {bid: recent[bid] for bid in blocker_ids}
    return blocker_id_map, name_map, date_map


def family_block_for(beneficiary_id, blocker_id_map, name_map):
    """Given the maps from :func:`household_cooldown`, return the name of a
    family member (other than this beneficiary) who blocks them, or ``None``."""
    blocker = blocker_id_map.get(beneficiary_id)
    if blocker is None or blocker == beneficiary_id:
        return None
    return name_map.get(blocker)
