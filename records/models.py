from django.db import models
from django.contrib.auth.models import User


class GrantRecord(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("released", "Released"),
        ("cancelled", "Cancelled"),
    ]

    beneficiary = models.ForeignKey(
        "beneficiaries.Beneficiary", on_delete=models.PROTECT, related_name="grants"
    )
    program = models.ForeignKey(
        "programs.AssistanceProgram", on_delete=models.PROTECT, related_name="grants"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_granted = models.DateField()
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_granted", "-created_at"]

    def __str__(self):
        return f"{self.beneficiary} — {self.program.name} ({self.date_granted})"
