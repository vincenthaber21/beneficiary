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


class Beneficiary(models.Model):
    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

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
