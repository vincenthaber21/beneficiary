import calendar
import json
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from utils import admin_required


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_int(value, minimum=None, maximum=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if minimum is not None and n < minimum:
        return None
    if maximum is not None and n > maximum:
        return None
    return n


def _resolve_dashboard_range(request, today):
    """Resolve date_from / date_to from GET params.

    Priority:
      1. Custom date_from / date_to
      2. Year / month / day preset
      3. No filter (entire history)
    """
    date_from = _parse_date(request.GET.get("date_from"))
    date_to = _parse_date(request.GET.get("date_to"))
    year = _parse_int(request.GET.get("year"), 2000, today.year + 1)
    month = _parse_int(request.GET.get("month"), 1, 12)
    day = _parse_int(request.GET.get("day"), 1, 31)

    filter_mode = "all"
    label = "All time"

    if date_from or date_to:
        filter_mode = "custom"
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
        if date_from and date_to:
            label = f"{date_from:%b %d, %Y} to {date_to:%b %d, %Y}"
        elif date_from:
            label = f"From {date_from:%b %d, %Y}"
        else:
            label = f"Until {date_to:%b %d, %Y}"
        year = month = day = None
    elif year:
        filter_mode = "preset"
        if month and day:
            last_day = calendar.monthrange(year, month)[1]
            day = min(day, last_day)
            date_from = date_to = date(year, month, day)
            label = f"{date_from:%b %d, %Y}"
        elif month:
            last_day = calendar.monthrange(year, month)[1]
            date_from = date(year, month, 1)
            date_to = date(year, month, last_day)
            label = f"{date_from:%B %Y}"
        else:
            date_from = date(year, 1, 1)
            date_to = date(year, 12, 31)
            label = str(year)
            day = None
    else:
        month = day = None

    return {
        "date_from": date_from,
        "date_to": date_to,
        "year": year,
        "month": month,
        "day": day,
        "filter_mode": filter_mode,
        "filter_label": label,
        "is_filtered": filter_mode != "all",
    }


def _apply_date_range(qs, field, date_from, date_to):
    if date_from:
        qs = qs.filter(**{f"{field}__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{field}__lte": date_to})
    return qs


def _build_bar_series(today, date_from, date_to, filter_mode):
    """Build bar chart labels/data based on the active date filter."""
    from records.models import GrantRecord

    bar_labels = []
    bar_data = []
    chart_subtitle = "Last 6 months"
    chart_title = "Monthly Grants Released"

    if filter_mode == "all" or (not date_from and not date_to):
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - relativedelta(months=i)
            next_month = month_date + relativedelta(months=1)
            count = GrantRecord.objects.filter(
                status="released",
                date_granted__gte=month_date,
                date_granted__lt=next_month,
            ).count()
            bar_labels.append(month_date.strftime("%b %Y"))
            bar_data.append(count)
        return bar_labels, bar_data, chart_title, chart_subtitle

    start = date_from or date(2000, 1, 1)
    end = date_to or today
    if start > end:
        start, end = end, start
    span_days = (end - start).days + 1

    if span_days <= 1:
        chart_title = "Grants Released"
        chart_subtitle = start.strftime("%b %d, %Y")
        count = GrantRecord.objects.filter(
            status="released", date_granted=start
        ).count()
        bar_labels = [start.strftime("%b %d")]
        bar_data = [count]
    elif span_days <= 45:
        chart_title = "Daily Grants Released"
        chart_subtitle = f"{start:%b %d} to {end:%b %d, %Y}"
        cursor = start
        while cursor <= end:
            count = GrantRecord.objects.filter(
                status="released", date_granted=cursor
            ).count()
            bar_labels.append(cursor.strftime("%b %d"))
            bar_data.append(count)
            cursor += timedelta(days=1)
    elif span_days <= 400:
        chart_title = "Monthly Grants Released"
        chart_subtitle = f"{start:%b %Y} to {end:%b %Y}"
        cursor = start.replace(day=1)
        end_month = end.replace(day=1)
        while cursor <= end_month:
            next_month = cursor + relativedelta(months=1)
            period_start = max(cursor, start)
            period_end = min(next_month - timedelta(days=1), end)
            count = GrantRecord.objects.filter(
                status="released",
                date_granted__gte=period_start,
                date_granted__lte=period_end,
            ).count()
            bar_labels.append(cursor.strftime("%b %Y"))
            bar_data.append(count)
            cursor = next_month
    else:
        chart_title = "Yearly Grants Released"
        chart_subtitle = f"{start.year} to {end.year}"
        for y in range(start.year, end.year + 1):
            y_start = max(date(y, 1, 1), start)
            y_end = min(date(y, 12, 31), end)
            count = GrantRecord.objects.filter(
                status="released",
                date_granted__gte=y_start,
                date_granted__lte=y_end,
            ).count()
            bar_labels.append(str(y))
            bar_data.append(count)

    return bar_labels, bar_data, chart_title, chart_subtitle


@login_required
def dashboard(request):
    from beneficiaries.models import Beneficiary
    from citizens.barangays import normalize_barangay_name
    from citizens.models import Barangay, Citizen
    from programs.models import AssistanceProgram
    from records.models import GrantRecord

    today = timezone.now().date()
    flt = _resolve_dashboard_range(request, today)
    date_from = flt["date_from"]
    date_to = flt["date_to"]

    citizens_qs = _apply_date_range(
        Citizen.objects.all(),
        "date_registered",
        date_from,
        date_to,
    )
    beneficiaries_qs = _apply_date_range(
        Beneficiary.objects.filter(is_active=True),
        "date_registered",
        date_from,
        date_to,
    )

    records_qs = _apply_date_range(
        GrantRecord.objects.all(),
        "date_granted",
        date_from,
        date_to,
    )
    released_qs = records_qs.filter(status="released")

    if flt["is_filtered"]:
        programs_qs = AssistanceProgram.objects.all()
        if date_to:
            programs_qs = programs_qs.filter(start_date__lte=date_to)
        if date_from:
            programs_qs = programs_qs.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=date_from)
            )
        total_programs = programs_qs.count()
        active_programs = programs_qs.filter(is_active=True).count()
    else:
        total_programs = AssistanceProgram.objects.count()
        active_programs = AssistanceProgram.objects.filter(is_active=True).count()

    total_citizens = citizens_qs.count()
    total_beneficiaries = beneficiaries_qs.count()
    claimed_ids = GrantRecord.objects.filter(status="released").values("beneficiary_id")
    not_yet_claimed = beneficiaries_qs.exclude(id__in=claimed_ids).count()
    # Male / Female = distinct beneficiaries who claimed (released grant) by sex
    claimed_in_period_ids = released_qs.values("beneficiary_id")
    male_count = (
        Beneficiary.objects.filter(id__in=claimed_in_period_ids, sex="M")
        .distinct()
        .count()
    )
    female_count = (
        Beneficiary.objects.filter(id__in=claimed_in_period_ids, sex="F")
        .distinct()
        .count()
    )
    vulnerable_count = (
        citizens_qs.exclude(vulnerable_groups=[])
        .exclude(vulnerable_groups__isnull=True)
        .count()
    )
    assistance_pct = (
        (total_beneficiaries / total_citizens * 100) if total_citizens else 0
    )
    total_records = records_qs.count()
    released_in_period = released_qs.count()

    recent_records = (
        records_qs.select_related("beneficiary", "program", "granted_by")
        .order_by("-date_granted", "-created_at")[:8]
    )

    class_rows = (
        beneficiaries_qs.values("beneficiary_class")
        .annotate(count=Count("id"))
        .order_by("beneficiary_class")
    )
    class_counts = {row["beneficiary_class"]: row["count"] for row in class_rows}

    bar_labels, bar_data, chart_title, chart_subtitle = _build_bar_series(
        today, date_from, date_to, flt["filter_mode"]
    )

    pie_labels = list(class_counts.keys())
    pie_data = list(class_counts.values())

    # Beneficiaries vs Claimed vs Unclaimed by barangay
    brgy_labels = list(
        Barangay.objects.filter(is_active=True)
        .order_by("name")
        .values_list("name", flat=True)
    )
    ben_by_brgy = {name: 0 for name in brgy_labels}
    claimed_by_brgy = {name: 0 for name in brgy_labels}

    def _bump(mapping, raw_name, n):
        key = normalize_barangay_name(raw_name)
        if not key:
            return
        if key not in mapping:
            brgy_labels.append(key)
            ben_by_brgy[key] = 0
            claimed_by_brgy[key] = 0
            mapping[key] = 0
        mapping[key] += n

    for row in (
        beneficiaries_qs.exclude(barangay="")
        .values("barangay")
        .annotate(count=Count("id"))
    ):
        _bump(ben_by_brgy, row["barangay"], row["count"])

    claimed_ids = released_qs.values("beneficiary_id")
    for row in (
        beneficiaries_qs.filter(id__in=claimed_ids)
        .exclude(barangay="")
        .values("barangay")
        .annotate(count=Count("id"))
    ):
        _bump(claimed_by_brgy, row["barangay"], row["count"])

    brgy_beneficiaries = [ben_by_brgy.get(name, 0) for name in brgy_labels]
    brgy_claimed = [claimed_by_brgy.get(name, 0) for name in brgy_labels]
    brgy_unclaimed = [
        max(0, ben_by_brgy.get(name, 0) - claimed_by_brgy.get(name, 0))
        for name in brgy_labels
    ]

    years = set()
    for y in GrantRecord.objects.dates("date_granted", "year"):
        years.add(y.year)
    for y in Beneficiary.objects.dates("date_registered", "year"):
        years.add(y.year)
    for y in Citizen.objects.dates("date_registered", "year"):
        years.add(y.year)
    years.add(today.year)
    year_choices = sorted(years, reverse=True)

    month_choices = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December"),
    ]
    day_choices = list(range(1, 32))

    context = {
        "total_citizens": total_citizens,
        "total_beneficiaries": total_beneficiaries,
        "not_yet_claimed": not_yet_claimed,
        "total_programs": total_programs,
        "male_count": male_count,
        "female_count": female_count,
        "assistance_pct": assistance_pct,
        "vulnerable_count": vulnerable_count,
        "active_programs": active_programs,
        "total_records": total_records,
        "released_this_month": released_in_period,
        "released_label": "In selected period" if flt["is_filtered"] else "All released",
        "recent_records": recent_records,
        "class_counts": class_counts,
        "bar_labels_json": json.dumps(bar_labels),
        "bar_data_json": json.dumps(bar_data),
        "pie_labels_json": json.dumps(pie_labels),
        "pie_data_json": json.dumps(pie_data),
        "brgy_labels_json": json.dumps(brgy_labels),
        "brgy_beneficiaries_json": json.dumps(brgy_beneficiaries),
        "brgy_claimed_json": json.dumps(brgy_claimed),
        "brgy_unclaimed_json": json.dumps(brgy_unclaimed),
        "chart_title": chart_title,
        "chart_subtitle": chart_subtitle,
        "filter_year": flt["year"] or "",
        "filter_month": flt["month"] or "",
        "filter_day": flt["day"] or "",
        "filter_date_from": (
            date_from.isoformat() if date_from and flt["filter_mode"] == "custom" else ""
        ),
        "filter_date_to": (
            date_to.isoformat() if date_to and flt["filter_mode"] == "custom" else ""
        ),
        "filter_label": flt["filter_label"],
        "is_filtered": flt["is_filtered"],
        "filter_mode": flt["filter_mode"],
        "year_choices": year_choices,
        "month_choices": month_choices,
        "day_choices": day_choices,
    }
    return render(request, "core/dashboard.html", context)


@admin_required
def audit_trails(request):
    from django.core.paginator import Paginator

    from .models import AuditTrail

    qs = AuditTrail.objects.select_related("user").all()

    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()
    module = (request.GET.get("module") or "").strip()
    username = (request.GET.get("username") or "").strip()
    success = (request.GET.get("success") or "").strip()
    date_from = _parse_date(request.GET.get("date_from"))
    date_to = _parse_date(request.GET.get("date_to"))

    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(description__icontains=q)
            | Q(path__icontains=q)
            | Q(ip_address__icontains=q)
            | Q(module__icontains=q)
        )
    if action:
        qs = qs.filter(action=action)
    if module:
        qs = qs.filter(module=module)
    if username:
        qs = qs.filter(username__icontains=username)
    if success == "1":
        qs = qs.filter(success=True)
    elif success == "0":
        qs = qs.filter(success=False)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    total_count = qs.count()
    login_count = qs.filter(action=AuditTrail.Action.LOGIN).count()
    logout_count = qs.filter(action=AuditTrail.Action.LOGOUT).count()
    failed_count = qs.filter(action=AuditTrail.Action.LOGIN_FAILED).count()
    module_open_count = qs.filter(action=AuditTrail.Action.MODULE_OPEN).count()

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    modules = (
        AuditTrail.objects.exclude(module="")
        .values_list("module", flat=True)
        .distinct()
        .order_by("module")
    )
    usernames = (
        AuditTrail.objects.exclude(username="")
        .values_list("username", flat=True)
        .distinct()
        .order_by("username")
    )

    context = {
        "page_obj": page_obj,
        "trails": page_obj.object_list,
        "total_count": total_count,
        "login_count": login_count,
        "logout_count": logout_count,
        "failed_count": failed_count,
        "module_open_count": module_open_count,
        "action_choices": AuditTrail.Action.choices,
        "modules": modules,
        "usernames": usernames,
        "filter_q": q,
        "filter_action": action,
        "filter_module": module,
        "filter_username": username,
        "filter_success": success,
        "filter_date_from": date_from.isoformat() if date_from else "",
        "filter_date_to": date_to.isoformat() if date_to else "",
    }
    return render(request, "core/audit_trails.html", context)
