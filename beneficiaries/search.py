"""Beneficiary list search: match every part of the name, in any order."""

from __future__ import annotations

import hashlib
import re

from django.core.cache import cache
from django.db.models import Case, IntegerField, Q, Value, When
from django.urls import reverse

from .models import Beneficiary

_SEARCH_CACHE_TTL = 60
_TOKEN_SPLIT = re.compile(r"[,./]+")
_NAME_FIELDS = (
    "last_name",
    "first_name",
    "middle_name",
    "citizen__last_name",
    "citizen__first_name",
    "citizen__middle_name",
    "citizen__suffix",
)


def _query_tokens(query):
    """Split a typed name into words. Commas and periods are separators."""
    cleaned = _TOKEN_SPLIT.sub(" ", (query or "").strip())
    return [token for token in cleaned.split() if token]


def _or_combine(parts):
    combined = parts[0]
    for part in parts[1:]:
        combined |= part
    return combined


def _name_match(token):
    """Match one word against first, middle, last, and the linked citizen suffix."""
    return _or_combine([
        Q(**{f"{field}__icontains": token}) for field in _NAME_FIELDS
    ])


def _any_token(lookup, tokens):
    combined = Q(**{lookup: tokens[0]})
    for token in tokens[1:]:
        combined |= Q(**{lookup: token})
    return combined


def person_label(beneficiary):
    """Full name: Last, First Middle Suffix."""
    middle = f" {beneficiary.middle_name}" if beneficiary.middle_name else ""
    suffix = ""
    citizen = beneficiary.citizen if beneficiary.citizen_id else None
    if citizen is not None and citizen.suffix:
        suffix = f" {citizen.suffix}"
    return f"{beneficiary.last_name}, {beneficiary.first_name}{middle}{suffix}".strip()


def filter_beneficiaries_by_query(qs, query):
    """
    Each word must match somewhere in the name (or an ID / contact field).

    "Angela Grace Abad" finds that person even when the words sit in
    different columns. A lone 1–2 character query stays a prefix match.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return qs

    for token in tokens:
        if len(token) <= 2 and len(tokens) == 1:
            qs = qs.filter(
                Q(last_name__istartswith=token)
                | Q(first_name__istartswith=token)
                | Q(middle_name__istartswith=token)
                | Q(citizen__suffix__istartswith=token)
                | Q(rfid_id__istartswith=token)
                | Q(citizen__registry_no__istartswith=token)
            )
        elif len(token) <= 2:
            qs = qs.filter(_name_match(token))
        else:
            qs = qs.filter(
                _name_match(token)
                | Q(rfid_id__icontains=token)
                | Q(contact_number__icontains=token)
                | Q(citizen__registry_no__icontains=token)
            )
    return qs


def order_beneficiaries_for_query(qs, query):
    """Put the closest name matches first (surname, then given name)."""
    tokens = _query_tokens(query)
    if not tokens:
        return qs.order_by("last_name", "first_name", "pk")

    return qs.annotate(
        name_rank=Case(
            When(_any_token("last_name__iexact", tokens), then=Value(0)),
            When(_any_token("last_name__istartswith", tokens), then=Value(1)),
            When(_any_token("first_name__istartswith", tokens), then=Value(2)),
            When(_any_token("middle_name__istartswith", tokens), then=Value(3)),
            When(_any_token("first_name__icontains", tokens), then=Value(4)),
            When(_any_token("middle_name__icontains", tokens), then=Value(5)),
            default=Value(8),
            output_field=IntegerField(),
        )
    ).order_by("name_rank", "last_name", "first_name", "pk")


def search_beneficiary_matches(query, limit=8):
    """Ranked beneficiary name matches for the list-page suggestions."""
    tokens = _query_tokens(query)
    if len("".join(tokens)) < 2:
        return [], 0

    limit = max(1, min(int(limit or 8), 20))
    epoch = cache.get("ben:list_search_epoch", 0)
    digest = hashlib.sha256(" ".join(tokens).casefold().encode()).hexdigest()[:20]
    cache_key = f"ben:list_search:v1:{epoch}:{digest}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached["results"], cached["total"]

    qs = order_beneficiaries_for_query(
        filter_beneficiaries_by_query(
            Beneficiary.objects.select_related("citizen"),
            " ".join(tokens),
        ),
        " ".join(tokens),
    )
    total = qs.count()
    results = []
    for beneficiary in qs[:limit]:
        citizen = beneficiary.citizen if beneficiary.citizen_id else None
        registry_no = ""
        if citizen is not None and citizen.registry_no:
            registry_no = citizen.registry_no
        elif beneficiary.rfid_id:
            registry_no = beneficiary.rfid_id
        name = person_label(beneficiary)
        results.append({
            "id": beneficiary.pk,
            "name": name,
            "registry_no": registry_no,
            "barangay": beneficiary.barangay or "",
            "sex": beneficiary.get_sex_display() if beneficiary.sex else "",
            "url": reverse("beneficiaries:detail", args=[beneficiary.pk]),
        })
    cache.set(cache_key, {"results": results, "total": total}, _SEARCH_CACHE_TTL)
    return results, total
