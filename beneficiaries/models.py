from django.db import models
from checker.logic import VALID_CLASSES

CLASS_CHOICES = [(c, c) for c in VALID_CLASSES]

RELATIONSHIP_CHOICES = [
    ("Spouse", "Spouse"),
    ("Child", "Child"),
    ("Parent", "Parent"),
    ("Sibling", "Sibling"),
    ("Grandparent", "Grandparent"),
    ("Grandchild", "Grandchild"),
    ("Other", "Other"),
]

# Citizen registry → locked eligibility fields (never trust client POST for these).
_INCOME_RANGE_DEFAULTS = {
    "0-15000": 7500,
    "15001-30000": 22500,
    "30001-50000": 40000,
    "50001-80000": 65000,
    "80001+": 80001,
}

_VULN_TO_CLASS = {
    "solo_parent": "Solo Parent",
    "pwd": "PWD",
    "senior": "Senior Citizen",
    "lactating": "Lactating Mother",
    "farmer": "Rice Farmer",
}

_OCC_TO_CLASS = {
    "farmer": "Rice Farmer",
    "laborer": "Construction Worker",
    "vendor": "Market Vendor",
    "driver": "Tricycle Driver",
}


def class_from_citizen(citizen):
    """Derive beneficiary_class from citizen vulnerable groups, then occupation."""
    if not citizen:
        return ""
    for g in citizen.vulnerable_groups or []:
        if g in _VULN_TO_CLASS:
            return _VULN_TO_CLASS[g]
    for occ in (
        getattr(citizen, "occupation_1", None),
        getattr(citizen, "occupation_2", None),
        getattr(citizen, "occupation_3", None),
    ):
        if occ in _OCC_TO_CLASS:
            return _OCC_TO_CLASS[occ]
    return ""


def income_from_citizen(citizen):
    """Derive monthly_income from citizen income_range. Returns None if unset."""
    if not citizen or not citizen.income_range:
        return None
    return _INCOME_RANGE_DEFAULTS.get(citizen.income_range)


def eligibility_from_citizen(citizen):
    """Return (beneficiary_class, monthly_income) locked from the citizen registry."""
    return class_from_citizen(citizen), income_from_citizen(citizen)


class Beneficiary(models.Model):
    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    # Master identity comes from the Citizen Registry — personal fields below are
    # kept as a synced cache so grants, ID cards, and eligibility stay fast.
    citizen = models.OneToOneField(
        "citizens.Citizen",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="beneficiary",
        verbose_name="Citizen",
        help_text="Linked citizen registry record. One citizen may only be enrolled once.",
    )
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    sex = models.CharField(
        max_length=1, choices=SEX_CHOICES, blank=True, verbose_name="Sex",
    )
    beneficiary_class = models.CharField(max_length=60, choices=CLASS_CHOICES)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    rfid_id = models.CharField(max_length=60, unique=True, null=True, blank=True, verbose_name="RFID / ID Number")
    signature = models.TextField(
        blank=True, default="",
        help_text="Beneficiary's signature captured on the ID form, stored as a "
                  "PNG data URL and printed on the e-Bahagi ID card.",
    )
    is_active = models.BooleanField(default=True)
    date_registered = models.DateField(auto_now_add=True)
    prior_grant_date = models.DateField(
        null=True, blank=True,
        verbose_name="Last grant received (prior to registration)",
        help_text="Date this person last received assistance from any program "
                  "before being added to this system. Used to enforce the 3-month cooldown.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        mid = f" {self.middle_name[0]}." if self.middle_name else ""
        return f"{self.first_name}{mid} {self.last_name}"

    def sync_from_citizen(self, citizen=None):
        """Copy identity, class, and income from the linked citizen registry entry.

        Program-specific fields (prior grant, notes, is_active) are left alone.
        Class and income are always taken from the citizen for security.
        """
        c = citizen or self.citizen
        if c is None:
            return
        self.citizen = c
        self.last_name = c.last_name
        self.first_name = c.first_name
        self.middle_name = c.middle_name or ""
        self.sex = c.sex or ""
        self.contact_number = c.contact_number or ""
        self.address = c.address or ""
        self.barangay = c.barangay or ""
        self.municipality = c.municipality or ""
        self.province = c.province or ""
        # Prefer citizen RFID tag; otherwise keep existing or use citizen ID.
        if c.rfid_tag:
            self.rfid_id = c.rfid_tag
        elif not self.rfid_id and c.registry_no:
            self.rfid_id = c.registry_no
        if c.signature:
            self.signature = c.signature
        ben_class = class_from_citizen(c)
        if ben_class:
            self.beneficiary_class = ben_class
        monthly = income_from_citizen(c)
        if monthly is not None:
            self.monthly_income = monthly

    def ensure_id_number(self):
        """Assign a unique e-Bahagi ID number to this beneficiary if it does
        not have one yet, then return it. Format: EB-<year>-<zero-padded pk>.
        Used so every beneficiary can be issued a tap-to-claim ID card."""
        if self.rfid_id:
            return self.rfid_id
        from django.utils import timezone
        year = timezone.now().year
        candidate = f"EB-{year}-{self.pk:05d}"
        # Guard against the (unlikely) collision with a manually entered ID.
        suffix = 0
        base = candidate
        while Beneficiary.objects.filter(rfid_id=candidate).exclude(pk=self.pk).exists():
            suffix += 1
            candidate = f"{base}-{suffix}"
        self.rfid_id = candidate
        self.save(update_fields=["rfid_id"])
        return self.rfid_id

    def last_grant_date(self):
        last = self.grants.filter(status="released").order_by("-date_granted").first()
        return last.date_granted if last else None

    def received_grant_within_months(self, months=3):
        from django.utils import timezone
        from datetime import timedelta
        # 90 days exactly (= COOLDOWN_DAYS in the JS) so server and client agree
        cutoff = timezone.now().date() - timedelta(days=months * 30)
        # Check grant records in the system
        if self.grants.filter(status="released", date_granted__gte=cutoff).exists():
            return True
        # Check manually recorded prior grant date (on OR after cutoff = in cooldown)
        if self.prior_grant_date and self.prior_grant_date >= cutoff:
            return True
        # Date BEFORE cutoff → cooldown has expired → not restricted
        return False


class FamilyMember(models.Model):
    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.CASCADE, related_name="family_members"
    )
    member = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="member_of",
        null=True,
        blank=True,
        verbose_name="Beneficiary",
    )
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    age = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["relationship"]

    def __str__(self):
        name = self.member.full_name if self.member_id else "(unset)"
        return f"{name} ({self.relationship})"


class BeneficiaryFingerprint(models.Model):
    """Registered fingerprint template for a beneficiary (one per finger)."""

    FINGER_CHOICES = [
        ("R_THUMB", "Right Thumb"),
        ("R_INDEX", "Right Index"),
        ("R_MIDDLE", "Right Middle"),
        ("R_RING", "Right Ring"),
        ("R_LITTLE", "Right Little"),
        ("L_THUMB", "Left Thumb"),
        ("L_INDEX", "Left Index"),
        ("L_MIDDLE", "Left Middle"),
        ("L_RING", "Left Ring"),
        ("L_LITTLE", "Left Little"),
    ]

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="fingerprints",
    )
    finger = models.CharField(
        max_length=12,
        choices=FINGER_CHOICES,
        verbose_name="Finger",
    )
    template_data = models.TextField(
        blank=True,
        default="",
        verbose_name="Fingerprint Template / ID",
        help_text=(
            "Template string or ID emitted by the fingerprint scanner. "
            "Used for matching at the ID / Fingerprint Tap station."
        ),
    )
    image_data = models.TextField(
        blank=True,
        default="",
        verbose_name="Fingerprint Image",
        help_text="Optional fingerprint image stored as a PNG data URL.",
    )
    quality = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Quality Score",
        help_text="Scanner quality score (0–100), if available.",
    )
    device_name = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Scanner Device",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Primary Finger",
        help_text="Preferred finger for quick lookup.",
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["beneficiary_id", "finger"]
        verbose_name = "Beneficiary Fingerprint"
        verbose_name_plural = "Beneficiary Fingerprints"
        constraints = [
            models.UniqueConstraint(
                fields=["beneficiary", "finger"],
                name="uniq_beneficiary_finger",
            ),
            models.UniqueConstraint(
                fields=["template_data"],
                condition=~models.Q(template_data=""),
                name="uniq_beneficiary_fp_template_data",
            ),
        ]
        indexes = [
            models.Index(fields=["template_data"]),
        ]

    def __str__(self):
        return f"{self.beneficiary} — {self.get_finger_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError

        from citizens.fingerprint_match import (
            find_duplicate_fingerprint,
            normalize_template,
        )

        super().clean()
        self.template_data = normalize_template(self.template_data)
        if not self.template_data:
            return
        owner, _fp, _dist = find_duplicate_fingerprint(
            self.template_data,
            exclude_beneficiary_fp_id=self.pk,
        )
        if owner:
            raise ValidationError(
                {
                    "template_data": (
                        f"This fingerprint is already registered to {owner}. "
                        "Each finger must be unique."
                    )
                }
            )

    @property
    def is_registered(self):
        return bool(self.template_data or self.image_data)
