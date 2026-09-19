from django.db import models


class AssistanceProgram(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2)
    income_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    grant_cooldown_months = models.PositiveIntegerField(default=3, help_text="Months before a beneficiary can receive another grant")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def grant_count(self):
        return self.grants.count()

    @property
    def total_released(self):
        return self.grants.filter(status="released").aggregate(
            total=models.Sum("amount")
        )["total"] or 0
