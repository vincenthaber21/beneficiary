from django import forms
from .models import AssistanceProgram


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
