from django import forms
from django.forms import inlineformset_factory

from citizens.models import get_barangay_choices

from .models import Beneficiary, FamilyMember, CLASS_CHOICES


class BeneficiaryForm(forms.ModelForm):
    barangay = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Barangay",
    )

    class Meta:
        model = Beneficiary
        fields = [
            "last_name", "first_name", "middle_name", "sex",
            "beneficiary_class", "monthly_income",
            "contact_number", "address", "barangay",
            "municipality", "province", "rfid_id",
            "signature", "prior_grant_date", "is_active", "notes",
        ]
        widgets = {
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Dela Cruz",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Juan",
            }),
            "middle_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Santos (optional)",
            }),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "beneficiary_class": forms.Select(attrs={"class": "form-select"}),
            "monthly_income": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": 0,
                "placeholder": "0.00",
            }),
            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 09xx-xxx-xxxx",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "House/Lot No., Street Name",
            }),
            "municipality": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Bacnotan",
            }),
            "province": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. La Union",
            }),
            "rfid_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Scan RFID or type ID number",
            }),
            "signature": forms.HiddenInput(),
            "prior_grant_date": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Select date…",
                "autocomplete": "off",
            }),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Any remarks or additional information about this beneficiary…",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = ""
        if self.instance and self.instance.pk:
            current = self.instance.barangay or ""
        self.fields["barangay"].choices = get_barangay_choices(
            include_blank=True, include_name=current or None
        )


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ["member", "relationship", "age"]
        widgets = {
            "member": forms.Select(attrs={
                "class": "form-select form-select-sm",
            }),
            "relationship": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "age": forms.NumberInput(attrs={
                "class": "form-control form-control-sm",
                "min": 0,
                "max": 120,
                "placeholder": "Age",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].empty_label = "— Select Beneficiary —"
        self.fields["member"].queryset = Beneficiary.objects.order_by("last_name", "first_name")
        self.fields["member"].required = True


FamilyMemberFormSet = inlineformset_factory(
    Beneficiary,
    FamilyMember,
    form=FamilyMemberForm,
    fk_name="beneficiary",
    extra=1,
    can_delete=True,
)
