from django import forms
from .models import GrantRecord
from beneficiaries.models import Beneficiary
from programs.models import AssistanceProgram


class GrantRecordForm(forms.ModelForm):
    class Meta:
        model = GrantRecord
        fields = ["beneficiary", "program", "amount", "date_granted", "status", "notes"]
        widgets = {
            "beneficiary": forms.Select(attrs={"class": "form-select"}),
            "program": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": 0,
                "placeholder": "0.00",
            }),
            "date_granted": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Select date…",
                "autocomplete": "off",
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Any remarks about this grant record…",
            }),
        }
