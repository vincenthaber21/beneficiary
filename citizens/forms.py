from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Citizen, CitizenFamilyMember, CitizenFingerprint, get_barangay_choices


class CitizenForm(forms.ModelForm):
    vulnerable_groups = forms.MultipleChoiceField(
        choices=Citizen.VULNERABLE_GROUP_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Vulnerable Group",
    )
    health_conditions = forms.MultipleChoiceField(
        choices=Citizen.HEALTH_CONDITION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Health Condition",
    )
    barangay = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Barangay",
    )

    class Meta:
        model = Citizen
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "suffix",
            "date_of_birth",
            "sex",
            "civil_status",
            "religion",
            "education",
            "contact_number",
            "rfid_tag",
            "address",
            "barangay",
            "municipality",
            "province",
            "income_range",
            "occupation_1",
            "occupation_2",
            "occupation_3",
            "vulnerable_groups",
            "health_conditions",
            "philsys_id",
            "voter_id",
            "other_id_type",
            "other_id_number",
            "email",
            "zip_code",
            "place_of_birth",
            "signature",
            "attachment",
            "status",
            "notes",
        ]
        widgets = {
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Middle name"}),
            "suffix": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jr., Sr., III"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "civil_status": forms.Select(attrs={"class": "form-select"}),
            "religion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Roman Catholic",
                "list": "religion-suggestions",
            }),
            "education": forms.Select(attrs={"class": "form-select"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "09XXXXXXXXX"}),
            "rfid_tag": forms.TextInput(attrs={"class": "form-control", "placeholder": "Scan or type RFID"}),
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Bldg / Hse / Unit No.",
            }),
            "municipality": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Bacnotan", "readonly": True,
            }),
            "province": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "La Union", "readonly": True,
            }),
            "income_range": forms.Select(attrs={"class": "form-select"}),
            "occupation_1": forms.Select(attrs={"class": "form-select"}),
            "occupation_2": forms.Select(attrs={"class": "form-select"}),
            "occupation_3": forms.Select(attrs={"class": "form-select"}),
            "philsys_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "National ID number"}),
            "voter_id": forms.TextInput(attrs={"class": "form-control"}),
            "other_id_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Driver's License"}),
            "other_id_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "place_of_birth": forms.TextInput(attrs={"class": "form-control", "placeholder": "City / Municipality"}),
            "signature": forms.HiddenInput(),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Optional notes"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = ""
        if self.instance and self.instance.pk:
            current = self.instance.barangay or ""
            self.fields["vulnerable_groups"].initial = self.instance.vulnerable_groups or []
            self.fields["health_conditions"].initial = self.instance.health_conditions or []
        self.fields["barangay"].choices = get_barangay_choices(
            include_blank=True, include_name=current or None
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vulnerable_groups = self.cleaned_data.get("vulnerable_groups") or []
        instance.health_conditions = self.cleaned_data.get("health_conditions") or []
        if commit:
            instance.save()
        return instance


class CitizenFamilyMemberForm(forms.ModelForm):
    class Meta:
        model = CitizenFamilyMember
        fields = ["member", "full_name", "relationship"]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "full_name": forms.TextInput(attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Full name (if not in registry)",
            }),
            "relationship": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Citizen.objects.order_by("last_name", "first_name")
        if self.instance and self.instance.citizen_id:
            qs = qs.exclude(pk=self.instance.citizen_id)
        self.fields["member"].queryset = qs
        self.fields["member"].required = False
        self.fields["full_name"].required = False
        self.fields["relationship"].required = False


CitizenFamilyFormSet = inlineformset_factory(
    Citizen,
    CitizenFamilyMember,
    form=CitizenFamilyMemberForm,
    fk_name="citizen",
    extra=1,
    can_delete=True,
)


class CitizenFingerprintForm(forms.ModelForm):
    class Meta:
        model = CitizenFingerprint
        fields = [
            "finger",
            "template_data",
            "image_data",
            "quality",
            "device_name",
            "is_primary",
        ]
        widgets = {
            "finger": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "template_data": forms.TextInput(attrs={
                "class": "form-control form-control-sm fp-template-input",
                "placeholder": "Place finger on scanner…",
                "autocomplete": "off",
                "spellcheck": "false",
                "inputmode": "none",
            }),
            "image_data": forms.HiddenInput(attrs={"class": "fp-image-input"}),
            "quality": forms.NumberInput(attrs={
                "class": "form-control form-control-sm",
                "min": 0,
                "max": 100,
                "placeholder": "0–100",
            }),
            "device_name": forms.TextInput(attrs={
                "class": "form-control form-control-sm fp-device-input",
                "placeholder": "Fingerprint Scanner",
            }),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["finger"].required = False
        self.fields["template_data"].required = False
        self.fields["image_data"].required = False
        self.fields["quality"].required = False
        self.fields["device_name"].required = False

    def clean(self):
        cleaned = super().clean()
        finger = cleaned.get("finger")
        template = (cleaned.get("template_data") or "").strip()
        image = (cleaned.get("image_data") or "").strip()
        quality = cleaned.get("quality")
        device = (cleaned.get("device_name") or "").strip()
        is_primary = cleaned.get("is_primary")
        has_data = bool(template or image or quality is not None or device or is_primary)

        if has_data and not finger:
            self.add_error("finger", "Select which finger was scanned.")
        if finger and not template and not image:
            self.add_error(
                "template_data",
                "Scan or enter a fingerprint template / ID for this finger.",
            )
        cleaned["template_data"] = template
        cleaned["image_data"] = image
        cleaned["device_name"] = device
        return cleaned


class BaseCitizenFingerprintFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        seen = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            finger = form.cleaned_data.get("finger")
            template = (form.cleaned_data.get("template_data") or "").strip()
            image = (form.cleaned_data.get("image_data") or "").strip()
            if not finger and not template and not image:
                continue
            if finger in seen:
                form.add_error("finger", "This finger is already listed.")
            else:
                seen.add(finger)


CitizenFingerprintFormSet = inlineformset_factory(
    Citizen,
    CitizenFingerprint,
    form=CitizenFingerprintForm,
    formset=BaseCitizenFingerprintFormSet,
    fk_name="citizen",
    extra=1,
    can_delete=True,
)
