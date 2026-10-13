"""Citizen registry search helpers (list page + typeahead pickers)."""

from __future__ import annotations

import hashlib
import re

from django.core.cache import cache
from django.db.models import Case, CharField, IntegerField, Q, Value, When
from django.db.models.functions import Cast
from django.urls import reverse

from .models import Citizen, HealthCondition, VulnerableGroup, catalog_choices

_SEARCH_CACHE_TTL = 60

# Free-text columns on the citizen list / registry.
_TEXT_FIELDS = (
    "registry_no",
    "last_name",
    "first_name",
    "middle_name",
    "suffix",
    "place_of_birth",
    "religion",
    "rfid_tag",
    "philsys_id",
    "voter_id",
    "other_id_type",
    "other_id_number",
    "contact_number",
    "email",
    "address",
    "barangay",
    "municipality",
    "province",
    "zip_code",
    "notes",
    "occupation_1",
    "occupation_2",
    "occupation_3",
    "civil_status",
    "education",
    "income_range",
    "status",
    "sex",
)

_NAME_FIELDS = ("last_name", "first_name", "middle_name", "suffix")
_TOKEN_SPLIT = re.compile(r"[,./]+")


def _query_tokens(query):
    """Split a typed name into words. Commas and periods are separators."""
    cleaned = _TOKEN_SPLIT.sub(" ", (query or "").strip())
    return [token for token in cleaned.split() if token]


def _person_label(citizen):
    """Full registry name: Last, First Middle Suffix."""
    middle = f" {citizen.middle_name}" if citizen.middle_name else ""
    suffix = f" {citizen.suffix}" if citizen.suffix else ""
    return f"{citizen.last_name}, {citizen.first_name}{middle}{suffix}".strip()


def _name_match(token):
    """Match one word against every name part (first, middle, last, suffix)."""
    return _or_combine([
        Q(**{f"{field}__icontains": token}) for field in _NAME_FIELDS
    ])


_CHOICE_FIELDS = (
    ("sex", Citizen.SEX_CHOICES),
    ("civil_status", Citizen.CIVIL_STATUS_CHOICES),
    ("status", Citizen.STATUS_CHOICES),
    ("education", Citizen.EDUCATION_CHOICES),
    ("income_range", Citizen.INCOME_RANGE_CHOICES),
    ("occupation_1", Citizen.OCCUPATION_CHOICES),
    ("occupation_2", Citizen.OCCUPATION_CHOICES),
    ("occupation_3", Citizen.OCCUPATION_CHOICES),
)


def _or_combine(parts):
    q_obj = parts[0]
    for part in parts[1:]:
        q_obj |= part
    return q_obj


def _choice_match(field, choices, token):
    """Match stored values and human-readable labels (e.g. Male → M).

    Uses equality / prefix — not bare substring — so \"male\" does not match Female.
    """
    parts = []
    t = token.casefold()
    for value, label in choices:
        if not value:
            continue
        value_cf = str(value).casefold()
        label_cf = str(label).casefold()
        if (
            t == value_cf
            or t == label_cf
            or value_cf.startswith(t)
            or label_cf.startswith(t)
        ):
            parts.append(Q(**{field: value}))
    if not parts:
        return None
    return _or_combine(parts)


def _token_match(token, include_dates=False):
    """OR-match one search token across all useful citizen columns."""
    parts = [Q(**{f"{field}__icontains": token}) for field in _TEXT_FIELDS]

    for field, choices in _CHOICE_FIELDS:
        choice_q = _choice_match(field, choices, token)
        if choice_q is not None:
            parts.append(choice_q)

    # JSON list fields (vulnerable groups / health conditions) — key or label.
    parts.append(Q(vulnerable_groups__icontains=token))
    parts.append(Q(health_conditions__icontains=token))
    t = token.casefold()
    for value, label in catalog_choices(
        VulnerableGroup, Citizen.VULNERABLE_GROUP_CHOICES
    ):
        value_cf = value.casefold()
        label_cf = label.casefold()
        if t == value_cf or t == label_cf or value_cf.startswith(t) or label_cf.startswith(t):
            parts.append(Q(vulnerable_groups__icontains=f'"{value}"'))
    for value, label in catalog_choices(
        HealthCondition, Citizen.HEALTH_CONDITION_CHOICES
    ):
        value_cf = value.casefold()
        label_cf = label.casefold()
        if t == value_cf or t == label_cf or value_cf.startswith(t) or label_cf.startswith(t):
            parts.append(Q(health_conditions__icontains=f'"{value}"'))

    if include_dates:
        # Dates as text (e.g. 1990, 2024-01-15) — requires Cast annotate.
        parts.append(Q(dob_text__icontains=token))
        parts.append(Q(registered_text__icontains=token))

    return _or_combine(parts)


def _identity_prefix_match(token):
    """Fast path for short tokens — uses indexed name / ID fields."""
    return (
        Q(last_name__istartswith=token)
        | Q(first_name__istartswith=token)
        | Q(middle_name__istartswith=token)
        | Q(registry_no__istartswith=token)
        | Q(contact_number__istartswith=token)
        | Q(rfid_tag__istartswith=token)
    )


def filter_citizens_by_query(qs, query):
    """
    Filter a Citizen queryset by free-text ``query``.

    Every word is matched on its own, so "Angela Grace Abad" finds that person
    even when the words sit in first, middle, and last name. A lone 1–2 character
    query stays a prefix match so it stays fast. Inside a longer name, short
    words such as "de" and "la" still match anywhere in the name.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return qs

    needs_dates = any(
        len(token) >= 3 and any(ch.isdigit() for ch in token) for token in tokens
    )
    if needs_dates:
        qs = qs.annotate(
            dob_text=Cast("date_of_birth", CharField()),
            registered_text=Cast("date_registered", CharField()),
        )

    for token in tokens:
        if len(token) <= 2 and len(tokens) == 1:
            qs = qs.filter(_identity_prefix_match(token))
        elif len(token) <= 2:
            qs = qs.filter(_name_match(token))
        else:
            qs = qs.filter(_token_match(token, include_dates=needs_dates))
    return qs


def _any_token(lookup, tokens):
    combined = Q(**{lookup: tokens[0]})
    for token in tokens[1:]:
        combined |= Q(**{lookup: token})
    return combined


def order_citizens_for_query(qs, query):
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


def search_citizen_matches(query, exclude_pk=None, limit=12):
    """
    Ranked matches for a typed name.

    Each word is matched against first, middle, last, and suffix, so
    "Angela Grace Abad" finds that citizen. Also matches registry no.,
    RFID, and contact when the word is long enough.

    Returns ``(results, total)``. ``results`` is capped at ``limit``.
    """
    tokens = _query_tokens(query)
    if len("".join(tokens)) < 2:
        return [], 0

    limit = max(1, min(int(limit or 12), 20))
    epoch = cache.get("citizen:search_epoch", 0)
    digest = hashlib.sha256(" ".join(tokens).casefold().encode()).hexdigest()[:20]
    cache_key = f"citizen:search:v3:{epoch}:{exclude_pk or 0}:{digest}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached["results"], cached["total"]

    qs = Citizen.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    if len(tokens) == 1 and len(tokens[0]) <= 2:
        token = tokens[0]
        qs = qs.filter(
            Q(last_name__istartswith=token)
            | Q(first_name__istartswith=token)
            | Q(middle_name__istartswith=token)
            | Q(suffix__istartswith=token)
            | Q(registry_no__istartswith=token)
        )
    else:
        for token in tokens:
            if len(token) <= 2:
                qs = qs.filter(_name_match(token))
            else:
                qs = qs.filter(
                    _name_match(token)
                    | Q(registry_no__icontains=token)
                    | Q(rfid_tag__icontains=token)
                    | Q(contact_number__icontains=token)
                )

    qs = order_citizens_for_query(qs, " ".join(tokens))
    total = qs.count()
    results = []
    for citizen in qs[:limit]:
        name = _person_label(citizen)
        results.append({
            "id": citizen.pk,
            "name": name,
            "label": f"{citizen.registry_no or '—'} — {name}",
            "registry_no": citizen.registry_no or "",
            "barangay": citizen.barangay or "",
            "sex": citizen.get_sex_display() if citizen.sex else "",
            "full_name": citizen.full_name,
            "url": reverse("citizens:detail", args=[citizen.pk]),
        })
    cache.set(cache_key, {"results": results, "total": total}, _SEARCH_CACHE_TTL)
    return results, total


def search_citizens(query, exclude_pk=None, limit=12):
    """Ranked citizen search by name / registry no. / RFID / contact."""
    results, _total = search_citizen_matches(
        query, exclude_pk=exclude_pk, limit=limit
    )
    return results
