from django import forms
from .models import AssistanceProgram


def months_between(start, end):
    """Whole months spanned by [start, end], minimum 1."""
    if not start or not end or end < start:
        return None
    days = (end - start).days
    return max(1, round(days / 30))


class AssistanceProgramForm(forms.ModelForm):
    class Meta:
        model = AssistanceProgram
        fields = ["name", "description", "budget", "income_threshold",
                  "grant_cooldown_months", "start_date", "end_date", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Ayuda sa Pangangailangan 2025",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Briefly describe the purpose, coverage and eligibility of this program…",
            }),
            "budget": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }),
            "income_threshold": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "15000.00",
            }),
            "grant_cooldown_months": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "3",
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "text",
                "placeholder": "YYYY-MM-DD",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "text",
                "placeholder": "YYYY-MM-DD (leave blank if ongoing)",
            }),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always derived/defaulted in clean() — avoid blocking submit on empty input.
        self.fields["grant_cooldown_months"].required = False
        self.fields["grant_cooldown_months"].widget.attrs.update({"min": "1"})

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after the start date.")
            return cleaned

        # Derive cooldown from program duration when an end date is set.
        derived = months_between(start, end)
        if derived is not None:
            cleaned["grant_cooldown_months"] = derived
        else:
            val = cleaned.get("grant_cooldown_months")
            if val in (None, ""):
                cleaned["grant_cooldown_months"] = 3
            elif val < 1:
                self.add_error("grant_cooldown_months", "Enter at least 1 month.")
        return cleaned
