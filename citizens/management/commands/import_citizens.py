"""
Management command: import_citizens
-----------------------------------
Load citizen registry rows from an Excel export into the Citizen model.

Usage:
    python manage.py import_citizens
    python manage.py import_citizens --path "C:\\Users\\...\\citizen_registry_data.xlsx"
    python manage.py import_citizens --dry-run
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from citizens.barangays import normalize_barangay_name
from citizens.models import Barangay, Citizen


DEFAULT_PATH = Path(r"C:\Users\cisnl\Downloads\citizen_registry_data.xlsx")

SEX_MAP = {
    "male": "M",
    "m": "M",
    "female": "F",
    "f": "F",
}

EDUCATION_MAP = {
    "early childhood education": "no_formal",
    "no formal education": "no_formal",
    "elementary level": "elementary",
    "elementary graduate": "elementary_grad",
    "junior high school level": "jhs",
    "junior high school graduate": "jhs_grad",
    "senior high school level": "shs",
    "senior high school graduate": "shs_grad",
    "post-secondary non-tertiary level": "vocational",
    "short-cycle tertiary level": "vocational",
    "vocational / technical": "vocational",
    "college level": "college",
    "college graduate": "college_grad",
    "masteral level": "postgrad",
    "doctoral level": "postgrad",
    "post-graduate": "postgrad",
}

CIVIL_STATUS_MAP = {
    "single": "single",
    "single/never married": "single",
    "never married": "single",
    "married": "married",
    "common law/live-in": "live_in",
    "common-law/live-in": "live_in",
    "live-in": "live_in",
    "common law": "live_in",
    "widowed": "widowed",
    "separated": "separated",
    "annulled": "annulled",
    "divorced": "divorced",
}

SUFFIX_MAP = {
    "jr": "Jr.",
    "jr.": "Jr.",
    "sr": "Sr.",
    "sr.": "Sr.",
    "ii": "II",
    "iii": "III",
    "iv": "IV",
    "v": "V",
}

# First matching pattern wins.
OCCUPATION_PATTERNS = [
    ("fisherfolk", re.compile(r"FISHER|AQUA.?CULTURE|FISHING", re.I)),
    ("farmer", re.compile(
        r"FARMER|FARM WORK|FARMHAND|HOG RAISING|CROP FARM|RICE FARM|"
        r"VEGETABLE|LIVESTOCK|POULTRY|CORN FARM|TOBACCO|ANIMAL PRODUCER|"
        r"SKILLED FARM",
        re.I,
    )),
    ("driver", re.compile(r"\bDRIVER\b|TRICYCLE|JEEPNEY|CHAUFFEUR|BUS AND TRAM", re.I)),
    ("vendor", re.compile(
        r"VENDOR|SALESPERSON|SHOPKEEPER|SALESMAN|SALESLADY|GROCER|"
        r"STREET FOOD|SHOP ASSISTANT|SALES CLERK|SALES HELPER|STORE SALES|"
        r"STALL AND MARKET|SHOP SALES",
        re.I,
    )),
    ("domestic", re.compile(
        r"DOMESTIC|HOUSEMAID|HOUSEBOY|HOUSEKEEPER|BABYSITTER|LAUNDERER|"
        r"CHILD CARE|NANNY|HOUSEHOLD SERVICE",
        re.I,
    )),
    ("laborer", re.compile(
        r"LABORER|CONSTRUCTION|CARPENTER|PAINTER|MASON|WELDER|BRICKLAYER|"
        r"JANITOR|CARETAKER|HELPER, CONSTRUCTION",
        re.I,
    )),
    ("government", re.compile(
        r"BARANGAY|LEGISLATOR|POLICE|GOVERNMENT|SANGGUNIANG|"
        r"BARANGAY CHAIRMAN|BARANGAY CAPTAIN|CIVIL SERVICE",
        re.I,
    )),
    ("ofw", re.compile(r"\bOFW\b|OVERSEAS", re.I)),
    ("student", re.compile(r"\bSTUDENT\b", re.I)),
    ("housewife", re.compile(r"HOUSEWIFE|HOMEMAKER", re.I)),
    ("retired", re.compile(r"RETIRED|PENSIONER", re.I)),
    ("unemployed", re.compile(r"UNEMPLOYED|NO OCCUPATION", re.I)),
    ("self_employed", re.compile(r"MANAGER|PROPRIETOR|CONTRACTOR|SELF.?EMPLOY", re.I)),
    ("private", re.compile(
        r"TEACHER|CLERK|CASHIER|CALL CENTER|NURSE|OFFICE|SECURITY|COOK|"
        r"WAITER|WAITRESS|PROFESSOR|ACCOUNTANT|ENGINEER|SECRETARY|"
        r"RECEPTIONIST|GUARD|BARISTA|DELIVERY",
        re.I,
    )),
]


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _title_name(value):
    text = _cell(value)
    if not text:
        return ""
    return " ".join(part.capitalize() for part in text.split())


def _map_sex(value):
    return SEX_MAP.get(_cell(value).lower(), "")


def _map_education(value):
    return EDUCATION_MAP.get(_cell(value).lower(), "")


def _map_civil_status(value):
    return CIVIL_STATUS_MAP.get(_cell(value).lower(), "")


def _map_suffix(value):
    raw = _cell(value)
    if not raw:
        return ""
    return SUFFIX_MAP.get(raw.lower(), raw)


def _map_occupation(value):
    raw = _cell(value)
    if not raw:
        return ""
    for code, pattern in OCCUPATION_PATTERNS:
        if pattern.search(raw):
            return code
    return "other"


def _map_religion(value):
    raw = _cell(value)
    if not raw:
        return ""
    lower = raw.lower()
    if lower in {"none", "don't know", "dont know", "unknown"}:
        return ""
    if raw.startswith("Roman Catholic"):
        return "Roman Catholic"
    if len(raw) > 120:
        return raw[:120]
    return raw


def _parse_birthdate(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _cell(value)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _parse_age(value, birthdate, today):
    if value not in (None, ""):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            pass
    if birthdate:
        years = today.year - birthdate.year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            years -= 1
        return years
    return None


def _vulnerable_groups(pwd, solo_parent, age):
    groups = []
    if _cell(pwd).lower() == "yes":
        groups.append("pwd")
    if _cell(solo_parent).lower() == "yes":
        groups.append("solo_parent")
    if age is not None and age >= 60:
        groups.append("senior")
    return groups


def _registry_no(citizen_id):
    raw = _cell(citizen_id)
    if not raw:
        return ""
    try:
        return str(int(float(raw)))
    except (TypeError, ValueError):
        return raw


def read_excel_citizens(filepath: str) -> list[dict]:
    try:
        import openpyxl
    except ImportError as exc:
        raise CommandError("openpyxl is required: pip install openpyxl") from exc

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        header = next(rows)
    except StopIteration as exc:
        wb.close()
        raise CommandError(f"Excel file is empty: {filepath}") from exc

    idx = {str(h).strip().lower(): i for i, h in enumerate(header) if h}
    required = ("firstname", "lastname")
    missing = [col for col in required if col not in idx]
    if missing:
        wb.close()
        raise CommandError(f"Missing required columns: {', '.join(missing)}")

    today = timezone.now().date()
    records = []
    for row in rows:
        first = _title_name(row[idx["firstname"]] if idx["firstname"] < len(row) else "")
        last = _title_name(row[idx["lastname"]] if idx["lastname"] < len(row) else "")
        if not first or not last:
            continue

        def col(name):
            if name not in idx or idx[name] >= len(row):
                return None
            return row[idx[name]]

        birthdate = _parse_birthdate(col("birthdate"))
        age = _parse_age(col("age"), birthdate, today)
        barangay = normalize_barangay_name(_cell(col("barangay")))
        records.append({
            "registry_no": _registry_no(col("citizen_id")),
            "first_name": first,
            "middle_name": _title_name(col("middlename")),
            "last_name": last,
            "suffix": _map_suffix(col("extname")),
            "date_of_birth": birthdate,
            "sex": _map_sex(col("gender")),
            "education": _map_education(col("educational attainment")),
            "civil_status": _map_civil_status(col("civil status")),
            "religion": _map_religion(col("religion")),
            "occupation_1": _map_occupation(col("psoc")),
            "barangay": barangay,
            "vulnerable_groups": _vulnerable_groups(col("pwd"), col("solo parent"), age),
            "_psoc": _cell(col("psoc")),
            "_age": age,
        })
    wb.close()
    return records


class Command(BaseCommand):
    help = "Import citizen registry rows from an Excel file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_PATH),
            help="Path to citizen_registry_data.xlsx",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )

    def handle(self, *args, **options):
        from collections import Counter

        path = Path(options["path"])
        dry_run = options["dry_run"]
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        self.stdout.write(f"Reading {path} ...")
        records = read_excel_citizens(str(path))
        self.stdout.write(f"Parsed {len(records):,} rows.")

        occ_counts = Counter(r["occupation_1"] or "(none)" for r in records)
        sex_counts = Counter(r["sex"] or "(none)" for r in records)
        civil_counts = Counter(r["civil_status"] or "(none)" for r in records)
        edu_counts = Counter(r["education"] or "(none)" for r in records)
        brgy_counts = Counter(r["barangay"] or "(none)" for r in records)
        vuln_counts = Counter(
            g for r in records for g in r["vulnerable_groups"]
        )

        self.stdout.write("\nOccupation mapping:")
        for key, n in occ_counts.most_common():
            self.stdout.write(f"  {key:16s} {n:6d}")
        self.stdout.write("\nSex:")
        for key, n in sex_counts.most_common():
            self.stdout.write(f"  {key:8s} {n:6d}")
        self.stdout.write("\nCivil status:")
        for key, n in civil_counts.most_common():
            self.stdout.write(f"  {key:12s} {n:6d}")
        self.stdout.write("\nEducation:")
        for key, n in edu_counts.most_common():
            self.stdout.write(f"  {key:16s} {n:6d}")
        self.stdout.write(f"\nBarangays: {len(brgy_counts)}")
        self.stdout.write("Vulnerable groups:")
        for key, n in vuln_counts.most_common():
            self.stdout.write(f"  {key:12s} {n:6d}")

        known_brgy = set(Barangay.objects.values_list("name", flat=True))
        unknown = sorted(b for b in brgy_counts if b and b not in known_brgy)
        if unknown:
            self.stdout.write(self.style.WARNING(
                f"Unknown barangays (will still be stored): {', '.join(unknown)}"
            ))

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run — no changes written."))
            return

        now = timezone.now()
        with transaction.atomic():
            existing = set(
                Citizen.objects.exclude(registry_no__isnull=True)
                .exclude(registry_no="")
                .values_list("registry_no", flat=True)
            )
            to_create = []
            skipped = 0
            seen = set(existing)
            for r in records:
                rid = r["registry_no"]
                if rid and rid in seen:
                    skipped += 1
                    continue
                if rid:
                    seen.add(rid)
                to_create.append(Citizen(
                    registry_no=rid or None,
                    first_name=r["first_name"],
                    middle_name=r["middle_name"],
                    last_name=r["last_name"],
                    suffix=r["suffix"],
                    date_of_birth=r["date_of_birth"],
                    sex=r["sex"],
                    civil_status=r["civil_status"],
                    religion=r["religion"],
                    education=r["education"],
                    occupation_1=r["occupation_1"],
                    barangay=r["barangay"],
                    municipality="Bacnotan",
                    province="La Union",
                    vulnerable_groups=r["vulnerable_groups"],
                    health_conditions=[],
                    status="active",
                    date_registered=now.date(),
                    created_at=now,
                    updated_at=now,
                ))
            Citizen.objects.bulk_create(to_create, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(to_create):,} citizens "
            f"({skipped:,} existing IDs skipped)."
        ))
        self.stdout.write(self.style.WARNING(
            "Monthly income was empty in the source file, so income range was left blank."
        ))
