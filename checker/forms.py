from django import forms
from .logic import VALID_CLASSES

CLASS_CHOICES = [(c, c) for c in VALID_CLASSES] + [("None", "None of the above")]


class BeneficiaryForm(forms.Form):
    beneficiary_class = forms.ChoiceField(
        label="Beneficiary class",
        choices=CLASS_CHOICES,
        widget=forms.Select(attrs={"class": "field"}),
    )
    received_grant_within_3_months = forms.TypedChoiceField(
        label="Received a grant within the last 3 months?",
        choices=[(0, "No"), (1, "Yes")],
        coerce=lambda v: bool(int(v)),
        widget=forms.RadioSelect,
        initial=0,
    )
