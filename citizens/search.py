"""Cached citizen registry search for typeahead pickers."""

from __future__ import annotations

from django.core.cache import cache
from django.db.models import Case, IntegerField, Q, Value, When

from .models import Citizen

_SEARCH_CACHE_TTL = 60


def search_citizens(query, exclude_pk=None, limit=12):
    """
    Ranked citizen search by name / registry no. / RFID / contact.
    Short queries use prefix matching to keep results usable.
    """
    q = (query or "").strip()
    if len(q) < 2:
        return []

    epoch = cache.get("citizen:search_epoch", 0)
    cache_key = (
        f"citizen:search:{epoch}:{exclude_pk or 0}:{q.casefold()}:{limit}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = Citizen.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    if len(q) <= 2:
        match = (
            Q(last_name__istartswith=q)
            | Q(first_name__istartswith=q)
            | Q(registry_no__istartswith=q)
        )
    else:
        match = (
            Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(middle_name__icontains=q)
            | Q(registry_no__icontains=q)
            | Q(rfid_tag__icontains=q)
            | Q(contact_number__icontains=q)
        )

    qs = (
        qs.filter(match)
        .annotate(
            rank=Case(
                When(registry_no__iexact=q, then=Value(0)),
                When(registry_no__istartswith=q, then=Value(1)),
                When(last_name__istartswith=q, then=Value(2)),
                When(first_name__istartswith=q, then=Value(3)),
                When(last_name__icontains=q, then=Value(4)),
                When(first_name__icontains=q, then=Value(5)),
                default=Value(9),
                output_field=IntegerField(),
            )
        )
        .order_by("rank", "last_name", "first_name")[:limit]
    )

    results = []
    for c in qs:
        mid = f" {c.middle_name}" if c.middle_name else ""
        name = f"{c.last_name}, {c.first_name}{mid}"
        results.append({
            "id": c.pk,
            "name": name,
            "label": f"{c.registry_no or '—'} — {name}",
            "registry_no": c.registry_no or "",
            "barangay": c.barangay or "",
            "sex": c.get_sex_display() if c.sex else "",
            "full_name": c.full_name,
        })
    cache.set(cache_key, results, _SEARCH_CACHE_TTL)
    return results
