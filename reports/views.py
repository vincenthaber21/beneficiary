import csv
from collections import Counter

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from utils import admin_required, staff_required
from beneficiaries.models import Beneficiary
from records.models import GrantRecord
from programs.models import AssistanceProgram
from checker.logic import VALID_CLASSES, evaluate
from django.db.models import Sum, Count


@staff_required
def report_index(request):
    beneficiaries = Beneficiary.objects.all()
    records = GrantRecord.objects.select_related("beneficiary", "program")
    programs = AssistanceProgram.objects.all()

    total_ben = beneficiaries.count()
    active_ben = beneficiaries.filter(is_active=True).count()
    total_released = records.filter(status="released").aggregate(t=Sum("amount"))["t"] or 0
    released_count = records.filter(status="released").count()
    pending_count = records.filter(status="pending").count()

    by_class = (
        beneficiaries.filter(is_active=True)
        .values("beneficiary_class")
        .annotate(count=Count("id"))
        .order_by("beneficiary_class")
    )

    by_program = (
        records.filter(status="released")
        .values("program__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    recent = records.order_by("-date_granted")[:20]

    return render(request, "reports/index.html", {
        "total_ben": total_ben,
        "active_ben": active_ben,
        "total_released": total_released,
        "released_count": released_count,
        "pending_count": pending_count,
        "by_class": by_class,
        "by_program": by_program,
        "recent": recent,
    })


@staff_required
def export_beneficiaries(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="beneficiaries.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "ID", "Last Name", "First Name", "Middle Name", "Class",
        "Monthly Income", "Contact", "Barangay", "Municipality",
        "Province", "RFID ID", "Active", "Date Registered",
    ])
    for b in Beneficiary.objects.all():
        writer.writerow([
            b.pk, b.last_name, b.first_name, b.middle_name,
            b.beneficiary_class, b.monthly_income, b.contact_number,
            b.barangay, b.municipality, b.province,
            b.rfid_id or "", "Yes" if b.is_active else "No",
            b.date_registered,
        ])
    return response


@admin_required
def import_from_excel(request):
    """Trigger the import_beneficiaries management command from the web UI."""
    import os
    import glob
    from django.conf import settings
    from beneficiaries.management.commands.import_beneficiaries import (
        read_excel_beneficiaries, _detect_class
    )

    folder = os.path.join(settings.BASE_DIR, "Final data")
    xlsx_files = sorted(glob.glob(os.path.join(folder, "*.xlsx")))

    if request.method == "POST":
        action = request.POST.get("action", "import")
        all_records = []
        for fp in xlsx_files:
            all_records.extend(read_excel_beneficiaries(fp))

        classified = []
        for r in all_records:
            cls = _detect_class(r["_occupation"], r["_id_number"])
            if cls:
                r["beneficiary_class"] = cls
                classified.append(r)

        with transaction.atomic():
            existing_keys = set(
                Beneficiary.objects.values_list("last_name", "first_name", "barangay")
            )
            used_rfids = set(
                Beneficiary.objects.exclude(rfid_id__isnull=True)
                .exclude(rfid_id="")
                .values_list("rfid_id", flat=True)
            )
            to_create = []
            skipped = 0
            for r in classified:
                key = (r["last_name"], r["first_name"], r["barangay"])
                if key in existing_keys:
                    skipped += 1
                    continue
                existing_keys.add(key)
                rfid = r["rfid_id"] or None
                if rfid:
                    if rfid in used_rfids:
                        rfid = None
                    else:
                        used_rfids.add(rfid)
                to_create.append(Beneficiary(
                    last_name=r["last_name"], first_name=r["first_name"],
                    middle_name=r["middle_name"],
                    beneficiary_class=r["beneficiary_class"],
                    monthly_income=0.00,
                    barangay=r["barangay"], municipality=r["municipality"],
                    province=r["province"], rfid_id=rfid,
                    notes=r["notes"], is_active=True,
                ))
            Beneficiary.objects.bulk_create(to_create, batch_size=500)

        messages.success(
            request,
            f"Import complete: {len(to_create)} new beneficiaries added, "
            f"{skipped} duplicates skipped."
        )
        if skipped == 0 and len(to_create) == 0:
            messages.warning(request, "No new records were imported (all duplicates).")
        return redirect("reports:import_excel")

    # GET – show preview
    all_records = []
    file_stats = []
    for fp in xlsx_files:
        recs = read_excel_beneficiaries(fp)
        file_stats.append({"name": os.path.basename(fp), "count": len(recs)})
        all_records.extend(recs)

    classified = []
    for r in all_records:
        cls = _detect_class(r["_occupation"], r["_id_number"])
        if cls:
            r["beneficiary_class"] = cls
            classified.append(r)

    class_counts = Counter(r["beneficiary_class"] for r in classified)
    class_breakdown = [
        {"cls": c, "count": class_counts.get(c, 0)} for c in VALID_CLASSES
    ]
    qualified_count = sum(
        1 for r in classified
        if evaluate(r["beneficiary_class"], False, 0.00)["qualified"]
    )
    existing_count = Beneficiary.objects.count()

    return render(request, "reports/import_excel.html", {
        "file_stats": file_stats,
        "total_raw": len(all_records),
        "total_classified": len(classified),
        "total_unclassified": len(all_records) - len(classified),
        "class_breakdown": class_breakdown,
        "qualified_count": qualified_count,
        "existing_count": existing_count,
    })


def _export_grant_records_csv():
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="grant_records.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "ID", "Beneficiary", "Program", "Amount", "Date Granted",
        "Status", "Granted By", "Notes",
    ])
    for r in GrantRecord.objects.select_related("beneficiary", "program", "granted_by"):
        writer.writerow([
            r.pk, str(r.beneficiary), r.program.name, r.amount,
            r.date_granted, r.status,
            r.granted_by.username if r.granted_by else "",
            r.notes,
        ])
    return response


def _export_qualified_by_vulnerable_group_csv():
    """Qualified beneficiaries listed per vulnerable group (beneficiary class)."""
    from datetime import timedelta

    from django.utils import timezone

    from beneficiaries.household import family_block_for, household_cooldown
    from checker.logic import evaluate

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="qualified_beneficiaries_by_vulnerable_group.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([
        "Vulnerable Group", "ID", "Last Name", "First Name", "Middle Name",
        "Sex", "Monthly Income", "Contact", "Barangay", "Municipality",
        "Province", "RFID ID", "Date Registered", "Eligibility Reason",
    ])

    cutoff = timezone.now().date() - timedelta(days=90)
    recent_ids = set(
        GrantRecord.objects.filter(
            status="released", date_granted__gte=cutoff
        ).values_list("beneficiary_id", flat=True)
    )
    blocker_id_map, name_map, _ = household_cooldown(3)

    qs = Beneficiary.objects.filter(is_active=True).order_by(
        "beneficiary_class", "last_name", "first_name"
    )
    for b in qs:
        has_recent = (
            b.pk in recent_ids
            or (b.prior_grant_date is not None and b.prior_grant_date >= cutoff)
        )
        family_blocker = (
            None if has_recent else family_block_for(b.pk, blocker_id_map, name_map)
        )
        result = evaluate(
            beneficiary_class=b.beneficiary_class,
            received_grant_within_3_months=has_recent,
            monthly_income=float(b.monthly_income),
            household_blocker_name=family_blocker,
        )
        if not result["qualified"]:
            continue
        writer.writerow([
            b.beneficiary_class,
            b.pk,
            b.last_name,
            b.first_name,
            b.middle_name,
            b.get_sex_display() if b.sex else "",
            b.monthly_income,
            b.contact_number,
            b.barangay,
            b.municipality,
            b.province,
            b.rfid_id or "",
            b.date_registered,
            result.get("reason", ""),
        ])
    return response


def _export_not_received_assistance_csv():
    """Active beneficiaries who have never received a released grant."""
    claimed_ids = GrantRecord.objects.filter(status="released").values("beneficiary_id")
    qs = (
        Beneficiary.objects.filter(is_active=True)
        .exclude(id__in=claimed_ids)
        .order_by("beneficiary_class", "last_name", "first_name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="not_received_assistance.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([
        "Vulnerable Group", "ID", "Last Name", "First Name", "Middle Name",
        "Sex", "Monthly Income", "Contact", "Barangay", "Municipality",
        "Province", "RFID ID", "Date Registered", "Prior Grant Date",
    ])
    for b in qs:
        writer.writerow([
            b.beneficiary_class,
            b.pk,
            b.last_name,
            b.first_name,
            b.middle_name,
            b.get_sex_display() if b.sex else "",
            b.monthly_income,
            b.contact_number,
            b.barangay,
            b.municipality,
            b.province,
            b.rfid_id or "",
            b.date_registered,
            b.prior_grant_date or "",
        ])
    return response


@staff_required
def export_records(request):
    """Download a records report. Pass ?report= to choose the list type."""
    report = (request.GET.get("report") or "").strip().lower()
    if report in ("qualified_by_group", "qualified"):
        return _export_qualified_by_vulnerable_group_csv()
    if report in ("not_received", "not_claimed"):
        return _export_not_received_assistance_csv()
    return _export_grant_records_csv()
