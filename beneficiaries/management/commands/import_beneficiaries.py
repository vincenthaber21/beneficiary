"""
Management command: import_beneficiaries
----------------------------------------
Reads barangay-profile Excel files from the "Final data/" folder,
extracts household heads, maps occupation → beneficiary class using the
decision-tree categories, and bulk-creates Beneficiary records.

Usage:
    python manage.py import_beneficiaries
    python manage.py import_beneficiaries --dry-run
    python manage.py import_beneficiaries --path "path/to/folder"
    python manage.py import_beneficiaries --clear   # wipe existing before import
"""

import os
import re
import glob

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from beneficiaries.models import Beneficiary
from checker.logic import VALID_CLASSES, evaluate


# ── Occupation → Beneficiary-class keyword mapping ────────────────────────────
# Patterns are tested IN ORDER; first match wins.
_CLASS_PATTERNS = [
    # Solo Parent  – catch "S.P" suffix in ID number (handled separately) or occ
    ("Solo Parent",      re.compile(r"SOLO\s+PARENT", re.I)),
    # Tricycle Driver  – must come before generic "DRIVER"
    ("Tricycle Driver",  re.compile(r"TRICYCL|TRIC\.\s*DRIV|TRIYCL|TRICYC", re.I)),
    # Senior Citizen
    ("Senior Citizen",   re.compile(r"SENIOR\s+CITIZEN|SENIOR\s+CIT\b|^S\.?C\.?\s*$|^SENIOR\s*$", re.I)),
    # PWD
    ("PWD",              re.compile(r"^PWD\b", re.I)),
    # Construction Worker
    ("Construction Worker", re.compile(
        r"CONSTRUCTI|CONS\.\s*WORK|CONST\.\s*WORK|CONS\.WORK|CONST\.WORK|CONRUCTION\s+WORK|CONTRUCTION\s+WORK",
        re.I,
    )),
    # Rice Farmer
    ("Rice Farmer",      re.compile(r"^FARMER\b|^RICE\s+FARMER|^FARMING\b|^FARME\b|^FAEMER\b|^FARM\b", re.I)),
    # Market Vendor
    ("Market Vendor",    re.compile(r"\bVENDOR\b", re.I)),
    # Lactating Mother  – if explicitly labelled
    ("Lactating Mother", re.compile(r"LACTAT", re.I)),
]


def _detect_class(occupation: str, id_number: str) -> str | None:
    """Return the matching VALID_CLASS or None."""
    occ = (occupation or "").strip()
    id_num = (id_number or "").strip()

    # Solo Parent from ID-number suffix (e.g. "2300282  S.P")
    if re.search(r"\bS\.P\b", id_num, re.I):
        return "Solo Parent"

    if not occ:
        return None

    for cls, pattern in _CLASS_PATTERNS:
        if pattern.search(occ):
            return cls

    return None


# ── Per-file layout descriptors ────────────────────────────────────────────────
#
# Each descriptor maps logical field names to zero-based column indices.
# "header_rows" = number of rows to skip before data begins.
#
# Layout A  – Cabaroan, Guinabang, Nagsimbaanan, Sta. Rita, Last 5 barangays
#   Col: 0=barangay 1=ctrl 2=hh_no 3=last 4=first 5=middle 6=suffix
#        7=gender 8=birthdate 9=valid_id 10=id_number 11=civil_status
#        12=hh_family 13-16=family_members 17=fam_bday 18=age 19=occupation
#
# Layout B  – Narra  (no occupation or id_number columns)
#   Col: 0=barangay 1=ctrl 2=last 3=first 4=middle 5=suffix 6=hh_family
#
# Layout C  – Raois  (no occupation or id_number columns)
#   Col: 0=barangay 1=ctrl 2=hh_no 3=last 4=first 5=middle 6=hh_family

_LAYOUT_A = {
    "header_rows": 3,   # skip rows 1-3; data from row 4
    "barangay": 0, "ctrl": 1, "hh_no": 2,
    "last": 3, "first": 4, "middle": 5, "suffix": 6,
    "id_number": 10, "occupation": 19,
}
_LAYOUT_B = {
    "header_rows": 4,
    "barangay": 0, "ctrl": 1, "hh_no": None,
    "last": 2, "first": 3, "middle": 4, "suffix": 5,
    "id_number": None, "occupation": None,
}
_LAYOUT_C = {
    "header_rows": 2,
    "barangay": 0, "ctrl": 1, "hh_no": 2,
    "last": 3, "first": 4, "middle": 5, "suffix": None,
    "id_number": None, "occupation": None,
}


def _sniff_layout(filename: str):
    """Pick layout based on filename."""
    base = os.path.basename(filename).lower()
    if "narra" in base:
        return _LAYOUT_B
    if "raois" in base:
        return _LAYOUT_C
    return _LAYOUT_A


def _cell(row, idx):
    """Safe cell access – returns stripped string or None."""
    if idx is None or idx >= len(row):
        return None
    v = row[idx]
    if v is None:
        return None
    return str(v).strip() or None


def _parse_barangay_municipality(raw: str):
    """Split 'Cabaroan, Bacnotan, La Union' → (barangay, municipality, province)."""
    parts = [p.strip() for p in raw.split(",")]
    barangay   = parts[0] if len(parts) > 0 else ""
    municipality = parts[1] if len(parts) > 1 else ""
    province   = ", ".join(parts[2:]) if len(parts) > 2 else ""
    return barangay, municipality, province


# ── Main reader ────────────────────────────────────────────────────────────────

def read_excel_beneficiaries(filepath: str) -> list[dict]:
    """
    Parse one Excel file and return a list of raw beneficiary dicts
    (household heads only).
    """
    try:
        import openpyxl
    except ImportError:
        raise CommandError(
            "openpyxl is required: pip install openpyxl"
        )

    layout = _sniff_layout(filepath)
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    records = []
    for row_num, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if row_num <= layout["header_rows"]:
            continue

        barangay_raw = _cell(row, layout["barangay"])
        last  = _cell(row, layout["last"])
        first = _cell(row, layout["first"])

        # Household-head rows have a barangay value AND a last/first name
        if not barangay_raw or not last or not first:
            continue

        middle     = _cell(row, layout["middle"]) or ""
        occupation = _cell(row, layout["occupation"])
        id_number  = _cell(row, layout["id_number"])

        brgy, muni, prov = _parse_barangay_municipality(barangay_raw)

        records.append({
            "last_name":  last.title(),
            "first_name": first.title(),
            "middle_name": middle.title(),
            "barangay":   brgy,
            "municipality": muni,
            "province":   prov,
            "rfid_id":    id_number,
            "notes":      occupation or "",
            "_occupation": occupation,
            "_id_number":  id_number,
        })

    wb.close()
    return records


# ── Command ────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Import beneficiaries from barangay-profile Excel files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="Final data",
            help="Folder containing the .xlsx files (default: 'Final data/')",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing beneficiaries before importing.",
        )

    def handle(self, *args, **options):
        folder  = options["path"]
        dry_run = options["dry_run"]
        clear   = options["clear"]

        xlsx_files = glob.glob(os.path.join(folder, "*.xlsx"))
        if not xlsx_files:
            raise CommandError(f"No .xlsx files found in '{folder}'.")

        self.stdout.write(f"Found {len(xlsx_files)} file(s) in '{folder}'.\n")

        # Collect all raw records from every file
        all_records = []
        for fp in sorted(xlsx_files):
            recs = read_excel_beneficiaries(fp)
            self.stdout.write(
                f"  {os.path.basename(fp):40s}  {len(recs):4d} household heads"
            )
            all_records.extend(recs)

        self.stdout.write(f"\nTotal raw records : {len(all_records)}")

        # Classify each record
        classified, unclassified = [], []
        for r in all_records:
            cls = _detect_class(r["_occupation"], r["_id_number"])
            if cls:
                r["beneficiary_class"] = cls
                classified.append(r)
            else:
                unclassified.append(r)

        self.stdout.write(f"Classified        : {len(classified)}")
        self.stdout.write(f"Unclassified      : {len(unclassified)} (skipped)\n")

        # Class breakdown
        from collections import Counter
        counts = Counter(r["beneficiary_class"] for r in classified)
        self.stdout.write("Class breakdown:")
        for cls in VALID_CLASSES:
            self.stdout.write(f"  {cls:25s}: {counts.get(cls, 0)}")

        # Preview validation results (income=0 → all valid-class records qualify)
        qualified = [
            r for r in classified
            if evaluate(r["beneficiary_class"], False, 0.00)["qualified"]
        ]
        self.stdout.write(
            f"\nEligibility preview (income=0, no prior grants): "
            f"{len(qualified)}/{len(classified)} would be QUALIFIED\n"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run – no changes written."))
            return

        # --- Write to DB ---
        with transaction.atomic():
            if clear:
                deleted, _ = Beneficiary.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing beneficiaries."))

            # De-duplicate by (last_name, first_name, barangay) to avoid
            # re-importing the same person on subsequent runs.
            existing_keys = set(
                Beneficiary.objects.values_list("last_name", "first_name", "barangay")
            )

            # Pre-load ALL existing RFID values + track new ones in this batch
            # to catch both DB duplicates and within-batch duplicates.
            used_rfids = set(
                Beneficiary.objects.exclude(rfid_id__isnull=True)
                .exclude(rfid_id="")
                .values_list("rfid_id", flat=True)
            )

            to_create = []
            skipped_dup = 0
            for r in classified:
                key = (r["last_name"], r["first_name"], r["barangay"])
                if key in existing_keys:
                    skipped_dup += 1
                    continue
                existing_keys.add(key)

                # RFID uniqueness: blank out if already used in DB or earlier in batch
                rfid = r["rfid_id"] or None
                if rfid:
                    if rfid in used_rfids:
                        rfid = None
                    else:
                        used_rfids.add(rfid)

                to_create.append(Beneficiary(
                    last_name         = r["last_name"],
                    first_name        = r["first_name"],
                    middle_name       = r["middle_name"],
                    beneficiary_class = r["beneficiary_class"],
                    monthly_income    = 0.00,   # not available in source data
                    barangay          = r["barangay"],
                    municipality      = r["municipality"],
                    province          = r["province"],
                    rfid_id           = rfid,
                    notes             = r["notes"],
                    is_active         = True,
                ))

            Beneficiary.objects.bulk_create(to_create, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(to_create)} new beneficiaries "
            f"({skipped_dup} duplicates skipped)."
        ))
        self.stdout.write(
            self.style.WARNING(
                "NOTE: Monthly income was not available in source files and "
                "has been set to ₱0.00. Update individual records as needed."
            )
        )
