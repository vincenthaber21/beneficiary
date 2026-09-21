from django.db import models


class Citizen(models.Model):
    """Master citizen / resident registry entry."""

    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]
    CIVIL_STATUS_CHOICES = [
        ("single", "Single"),
        ("married", "Married"),
        ("live_in", "Common law / Live-in"),
        ("widowed", "Widowed"),
        ("separated", "Separated"),
        ("annulled", "Annulled"),
        ("divorced", "Divorced"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deceased", "Deceased"),
        ("moved", "Moved out"),
    ]
    EDUCATION_CHOICES = [
        ("", "—"),
        ("no_formal", "No formal education"),
        ("elementary", "Elementary level"),
        ("elementary_grad", "Elementary graduate"),
        ("jhs", "Junior high school level"),
        ("jhs_grad", "Junior high school graduate"),
        ("shs", "Senior high school level"),
        ("shs_grad", "Senior high school graduate"),
        ("vocational", "Vocational / Technical"),
        ("college", "College level"),
        ("college_grad", "College graduate"),
        ("postgrad", "Post-graduate"),
    ]
    INCOME_RANGE_CHOICES = [
        ("", "—"),
        ("0-15000", "Php 0.00 – Php 15,000.00"),
        ("15001-30000", "Php 15,001.00 – Php 30,000.00"),
        ("30001-50000", "Php 30,001.00 – Php 50,000.00"),
        ("50001-80000", "Php 50,001.00 – Php 80,000.00"),
        ("80001+", "Php 80,001.00 and above"),
    ]
    OCCUPATION_CHOICES = [
        ("", "—"),
        ("farmer", "Farmer"),
        ("fisherfolk", "Fisherfolk"),
        ("laborer", "Laborer / Construction"),
        ("vendor", "Vendor / Retail"),
        ("driver", "Driver"),
        ("domestic", "Domestic helper"),
        ("government", "Government employee"),
        ("private", "Private employee"),
        ("self_employed", "Self-employed"),
        ("ofw", "OFW"),
        ("student", "Student"),
        ("housewife", "Housewife / Homemaker"),
        ("retired", "Retired"),
        ("unemployed", "Unemployed"),
        ("other", "Other"),
    ]
    VULNERABLE_GROUP_CHOICES = [
        ("senior", "Senior Citizen"),
        ("pwd", "Person with Disability (PWD)"),
        ("solo_parent", "Solo Parent"),
        ("indigent", "Indigent"),
        ("pregnant", "Pregnant"),
        ("lactating", "Lactating Mother"),
        ("ip", "Indigenous People"),
        ("farmer", "Tobacco Farmer"),
        ("fisherfolk", "Fisherfolk"),
        ("youth", "Youth"),
        ("4ps", "4Ps Beneficiary"),
    ]
    HEALTH_CONDITION_CHOICES = [
        ("chronic", "Chronic Illness"),
        ("mental", "Mental Disability"),
        ("physical", "Physical Disability"),
        ("visual", "Visual Impairment"),
        ("hearing", "Hearing Impairment"),
        ("speech", "Speech Impairment"),
        ("diabetes", "Diabetes"),
        ("hypertension", "Hypertension"),
        ("cancer", "Cancer"),
        ("other", "Other"),
    ]

    # Identity
    registry_no = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        help_text="Auto-assigned if left blank (e.g. CR-2026-00001).",
        verbose_name="Citizen ID",
    )
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(
        max_length=20, blank=True, verbose_name="Ext. Name",
        help_text="Jr., Sr., III, etc.",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=200, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=True)
    civil_status = models.CharField(
        max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True
    )
    religion = models.CharField(max_length=120, blank=True)
    education = models.CharField(
        max_length=40,
        choices=EDUCATION_CHOICES,
        blank=True,
        verbose_name="Highest Educational Attainment",
    )
    rfid_tag = models.CharField(
        max_length=60, blank=True, verbose_name="RFID Tag",
    )

    # Government IDs
    philsys_id = models.CharField(
        max_length=30, blank=True, verbose_name="PhilSys ID (National ID)"
    )
    voter_id = models.CharField(max_length=40, blank=True, verbose_name="Voter's ID")
    other_id_type = models.CharField(max_length=60, blank=True)
    other_id_number = models.CharField(max_length=60, blank=True)

    # Contact & address
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(
        max_length=255, blank=True, verbose_name="Bldg / Hse / Unit No."
    )
    barangay = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Barangay",
        help_text="Select from the barangay list (manage list under Barangays).",
    )
    municipality = models.CharField(max_length=100, blank=True, default="Bacnotan")
    province = models.CharField(max_length=100, blank=True, default="La Union")
    zip_code = models.CharField(max_length=10, blank=True)

    # Work
    income_range = models.CharField(
        max_length=20,
        choices=INCOME_RANGE_CHOICES,
        blank=True,
        verbose_name="Monthly Income Range",
    )
    occupation_1 = models.CharField(
        max_length=40, choices=OCCUPATION_CHOICES, blank=True,
        verbose_name="Occupation 1",
    )
    occupation_2 = models.CharField(
        max_length=40, choices=OCCUPATION_CHOICES, blank=True,
        verbose_name="Occupation 2",
    )
    occupation_3 = models.CharField(
        max_length=40, choices=OCCUPATION_CHOICES, blank=True,
        verbose_name="Occupation 3",
    )

    # Classification lists (stored as JSON-friendly comma lists via MultiSelect)
    vulnerable_groups = models.JSONField(default=list, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)

    signature = models.TextField(
        blank=True,
        default="",
        help_text="Signature captured on the ID form, stored as a PNG data URL "
                  "and printed on the e-Bahagi ID card.",
    )
    attachment = models.FileField(
        upload_to="citizen_attachments/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Attachment",
    )

    # Registry meta
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    date_registered = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Citizen Registry"
        verbose_name_plural = "Citizen Registry"
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["barangay"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        mid = f" {self.middle_name}" if self.middle_name else ""
        suf = f" {self.suffix}" if self.suffix else ""
        return f"{self.first_name}{mid} {self.last_name}{suf}".strip()

    def vulnerable_labels(self):
        lookup = dict(self.VULNERABLE_GROUP_CHOICES)
        return [lookup.get(v, v) for v in (self.vulnerable_groups or [])]

    def health_labels(self):
        lookup = dict(self.HEALTH_CONDITION_CHOICES)
        return [lookup.get(v, v) for v in (self.health_conditions or [])]

    def ensure_id_number(self):
        """Assign a unique Citizen ID if missing, then return it.
        Format: CR-<year>-<zero-padded pk> (same as auto-assign on create)."""
        if self.registry_no:
            return self.registry_no
        from django.utils import timezone

        year = timezone.now().year
        candidate = f"CR-{year}-{self.pk:05d}"
        suffix = 0
        base = candidate
        while Citizen.objects.filter(registry_no=candidate).exclude(pk=self.pk).exists():
            suffix += 1
            candidate = f"{base}-{suffix}"
        self.registry_no = candidate
        self.save(update_fields=["registry_no"])
        return self.registry_no

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if not self.municipality:
            self.municipality = "Bacnotan"
        if not self.province:
            self.province = "La Union"
        super().save(*args, **kwargs)
        if creating and not self.registry_no:
            self.ensure_id_number()


class Barangay(models.Model):
    """Selectable barangay for citizen Current Address (can be added manually)."""

    name = models.CharField(max_length=100, unique=True)
    population = models.PositiveIntegerField(
        default=0,
        help_text="Census / reference population used on the dashboard chart.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Barangay"
        verbose_name_plural = "Barangays"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)


def get_barangay_choices(include_blank=True, include_name=None):
    """Return (value, label) pairs for barangay dropdowns."""
    names = list(
        Barangay.objects.filter(is_active=True)
        .order_by("name")
        .values_list("name", flat=True)
    )
    if include_name and include_name not in names:
        names = [include_name] + names
    choices = [(n, n) for n in names]
    if include_blank:
        return [("", "---------")] + choices
    return choices


class CitizenFamilyMember(models.Model):
    """Household / family composition entry for a citizen."""

    RELATIONSHIP_CHOICES = [
        ("Spouse", "Spouse"),
        ("Child", "Child"),
        ("Parent", "Parent"),
        ("Sibling", "Sibling"),
        ("Grandparent", "Grandparent"),
        ("Grandchild", "Grandchild"),
        ("In-law", "In-law"),
        ("Other", "Other"),
    ]

    citizen = models.ForeignKey(
        Citizen, on_delete=models.CASCADE, related_name="family_members"
    )
    member = models.ForeignKey(
        Citizen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_of",
        verbose_name="Citizen",
    )
    full_name = models.CharField(max_length=200, blank=True)
    relationship = models.CharField(
        max_length=40, choices=RELATIONSHIP_CHOICES, blank=True,
        verbose_name="Relationship to HH",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Family Member"
        verbose_name_plural = "Family Composition"

    def __str__(self):
        name = self.full_name or (self.member.full_name if self.member else "—")
        return f"{name} ({self.relationship or 'member'})"

    def display_name(self):
        if self.member_id:
            return self.member.full_name
        return self.full_name or "—"

    def display_citizen_id(self):
        if self.member_id and self.member.registry_no:
            return self.member.registry_no
        return "—"


class CitizenFingerprint(models.Model):
    """Registered fingerprint template for a citizen (one per finger)."""

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

    citizen = models.ForeignKey(
        Citizen,
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
        ordering = ["citizen_id", "finger"]
        verbose_name = "Citizen Fingerprint"
        verbose_name_plural = "Citizen Fingerprints"
        constraints = [
            models.UniqueConstraint(
                fields=["citizen", "finger"],
                name="uniq_citizen_finger",
            ),
            models.UniqueConstraint(
                fields=["template_data"],
                condition=~models.Q(template_data=""),
                name="uniq_citizen_fp_template_data",
            ),
        ]
        indexes = [
            models.Index(fields=["template_data"]),
        ]

    def __str__(self):
        return f"{self.citizen} — {self.get_finger_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError

        from .fingerprint_match import find_duplicate_fingerprint, normalize_template

        super().clean()
        self.template_data = normalize_template(self.template_data)
        if not self.template_data:
            return
        owner, _fp, _dist = find_duplicate_fingerprint(
            self.template_data,
            exclude_citizen_fp_id=self.pk,
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
