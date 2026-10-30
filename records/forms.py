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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].queryset = AssistanceProgram.objects.filter(
            is_active=True
        ).order_by("name")
        # If editing / beneficiary already known, limit to their assigned program.
        ben = None
        if self.is_bound:
            ben_id = self.data.get("beneficiary")
            if ben_id:
                ben = Beneficiary.objects.filter(pk=ben_id).select_related("program").first()
        elif self.instance and self.instance.pk and self.instance.beneficiary_id:
            ben = self.instance.beneficiary
        if ben and ben.program_id:
            self.fields["program"].queryset = AssistanceProgram.objects.filter(
                pk=ben.program_id
            )
            if not self.is_bound and not self.initial.get("program"):
                self.fields["program"].initial = ben.program_id

    def clean(self):
        cleaned = super().clean()
        ben = cleaned.get("beneficiary")
        program = cleaned.get("program")
        if ben and program and ben.program_id and program.pk != ben.program_id:
            self.add_error(
                "program",
                f"{ben.full_name} is enrolled only for “{ben.program.name}”. "
                "Choose that program, or change their enrollment on the beneficiary form.",
            )
        return cleaned
