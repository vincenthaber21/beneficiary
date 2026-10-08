"""Citizen registry search helpers (list page + typeahead pickers)."""

from __future__ import annotations

from django.core.cache import cache
from django.db.models import Case, CharField, IntegerField, Q, Value, When
from django.db.models.functions import Cast

from .models import Citizen

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
    for value, label in Citizen.VULNERABLE_GROUP_CHOICES:
        value_cf = value.casefold()
        label_cf = label.casefold()
        if t == value_cf or t == label_cf or value_cf.startswith(t) or label_cf.startswith(t):
            parts.append(Q(vulnerable_groups__icontains=f'"{value}"'))
    for value, label in Citizen.HEALTH_CONDITION_CHOICES:
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

    Multi-word queries are AND across tokens (each word must match somewhere),
    so "Juan Santos" finds Juan Santos even when the words are in different columns.
    Short tokens use prefix matching on identity fields for speed.
    """
    q = (query or "").strip()
    if not q:
        return qs

    tokens = [t for t in q.split() if t]
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
        if len(token) <= 2:
            qs = qs.filter(_identity_prefix_match(token))
        else:
            qs = qs.filter(_token_match(token, include_dates=needs_dates))
    return qs


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
