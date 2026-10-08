from django import forms
from django.core.cache import cache
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from decimal import Decimal

from citizens.models import Citizen, get_barangay_choices

from .models import (
    Beneficiary,
    BeneficiaryFingerprint,
    FamilyMember,
    CLASS_CHOICES,
    eligibility_from_citizen,
)

_AVAILABLE_COUNT_CACHE_TTL = 120
_CITIZEN_SEARCH_CACHE_TTL = 60


def available_citizens_qs(exclude_beneficiary_pk=None):
    """Citizens not already enrolled as a beneficiary (plus the current one on edit)."""
    qs = Citizen.objects.order_by("last_name", "first_name")
    taken = Beneficiary.objects.exclude(citizen__isnull=True)
    if exclude_beneficiary_pk:
        taken = taken.exclude(pk=exclude_beneficiary_pk)
    taken_ids = taken.values_list("citizen_id", flat=True)
    return qs.exclude(pk__in=taken_ids)


def available_citizen_count(exclude_beneficiary_pk=None):
    """Cached count of citizens still available to enroll."""
    key = f"ben:available_citizen_count:{exclude_beneficiary_pk or 0}"
    count = cache.get(key)
    if count is None:
        total = Citizen.objects.count()
        taken = Beneficiary.objects.exclude(citizen__isnull=True)
        if exclude_beneficiary_pk:
            taken = taken.exclude(pk=exclude_beneficiary_pk)
        count = max(0, total - taken.count())
        cache.set(key, count, _AVAILABLE_COUNT_CACHE_TTL)
    return count


def invalidate_citizen_enrollment_cache():
    """Drop cached available-count entries after enroll/unenroll."""
    # LocMemCache has no delete_pattern; clear both common keys + search prefix via version bump.
    cache.delete("ben:available_citizen_count:0")
    cache.set("ben:citizen_search_epoch", cache.get("ben:citizen_search_epoch", 0) + 1, None)
    cache.set("ben:family_search_epoch", cache.get("ben:family_search_epoch", 0) + 1, None)


def search_available_citizens(query, exclude_beneficiary_pk=None, limit=12):
    """
    Search enrollable citizens by name / registry no. / RFID.
    Short queries prefer name/ID prefix matches so results stay usable.
    Results are cached briefly for repeated keystrokes.
    """
    from django.db.models import Case, IntegerField, Value, When

    q = (query or "").strip()
    if len(q) < 2:
        return []

    epoch = cache.get("ben:citizen_search_epoch", 0)
    cache_key = (
        f"ben:citizen_search:{epoch}:{exclude_beneficiary_pk or 0}:"
        f"{q.casefold()}:{limit}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base = available_citizens_qs(exclude_beneficiary_pk)
    # 2-letter searches: prefix-only (avoids huge noisy "contains" lists).
    if len(q) <= 2:
        match = (
            Q(last_name__istartswith=q)
            | Q(first_name__istartswith=q)
            | Q(registry_no__istartswith=q)
        )
    else:
        match = (
            Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(middle_name__icontains=q)
            | Q(registry_no__icontains=q)
            | Q(rfid_tag__icontains=q)
            | Q(contact_number__icontains=q)
        )

    qs = (
        base.filter(match)
        .annotate(
            rank=Case(
                When(registry_no__iexact=q, then=Value(0)),
                When(registry_no__istartswith=q, then=Value(1)),
                When(last_name__istartswith=q, then=Value(2)),
                When(first_name__istartswith=q, then=Value(3)),
                When(last_name__icontains=q, then=Value(4)),
                When(first_name__icontains=q, then=Value(5)),
                default=Value(9),
                output_field=IntegerField(),
            )
        )
        .order_by("rank", "last_name", "first_name")[:limit]
    )

    results = []
    for c in qs:
        mid = f" {c.middle_name}" if c.middle_name else ""
        results.append({
            "id": c.pk,
            "name": f"{c.last_name}, {c.first_name}{mid}",
            "label": (
                f"{c.registry_no or '—'} — {c.last_name}, {c.first_name}"
                + (f" {c.middle_name}" if c.middle_name else "")
            ),
            "registry_no": c.registry_no or "",
            "barangay": c.barangay or "",
            "sex": c.get_sex_display() if c.sex else "",
        })
    cache.set(cache_key, results, _CITIZEN_SEARCH_CACHE_TTL)
    return results


def search_beneficiaries(query, exclude_pk=None, exclude_citizen_pk=None, limit=12):
    """
    Family-member typeahead — same registry search as Citizens → Family Composition.

    Returns citizen matches ranked with enrolled beneficiaries first.
    ``id`` is the beneficiary PK when ``can_link`` is True (form stores Beneficiary FK);
    otherwise ``id`` is null and the row is shown as not-yet-enrolled.
    """
    from datetime import date
    from django.db.models import Case, IntegerField, Value, When

    from citizens.models import Citizen

    q = (query or "").strip()
    if len(q) < 2:
        return []

    epoch = cache.get("ben:family_search_epoch", 0)
    cache_key = (
        f"ben:family_search:{epoch}:{exclude_pk or 0}:"
        f"{exclude_citizen_pk or 0}:{q.casefold()}:{limit}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Resolve which citizen to hide when editing an existing beneficiary.
    if exclude_citizen_pk is None and exclude_pk:
        exclude_citizen_pk = (
            Beneficiary.objects.filter(pk=exclude_pk)
            .values_list("citizen_id", flat=True)
            .first()
        )

    qs = Citizen.objects.all()
    if exclude_citizen_pk:
        qs = qs.exclude(pk=exclude_citizen_pk)

    if len(q) <= 2:
        match = (
            Q(last_name__istartswith=q)
            | Q(first_name__istartswith=q)
            | Q(registry_no__istartswith=q)
        )
    else:
        match = (
            Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(middle_name__icontains=q)
            | Q(registry_no__icontains=q)
            | Q(rfid_tag__icontains=q)
            | Q(contact_number__icontains=q)
        )

    # Prefer already-enrolled citizens so linkable rows float to the top.
    enrolled_ids = set(
        Beneficiary.objects.exclude(citizen__isnull=True)
        .exclude(pk=exclude_pk)
        .values_list("citizen_id", flat=True)
    )

    qs = (
        qs.filter(match)
        .annotate(
            rank=Case(
                When(registry_no__iexact=q, then=Value(0)),
                When(registry_no__istartswith=q, then=Value(1)),
                When(last_name__istartswith=q, then=Value(2)),
                When(first_name__istartswith=q, then=Value(3)),
                When(last_name__icontains=q, then=Value(4)),
                When(first_name__icontains=q, then=Value(5)),
                default=Value(9),
                output_field=IntegerField(),
            ),
            enrolled_first=Case(
                When(pk__in=enrolled_ids, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        .order_by("enrolled_first", "rank", "last_name", "first_name")[:limit]
    )

    ben_by_citizen = {
        b.citizen_id: b
        for b in Beneficiary.objects.filter(
            citizen_id__in=[c.pk for c in qs]
        ).exclude(pk=exclude_pk)
    }

    today = date.today()
    results = []
    for c in qs:
        mid = f" {c.middle_name}" if c.middle_name else ""
        name = f"{c.last_name}, {c.first_name}{mid}"
        ben = ben_by_citizen.get(c.pk)
        age = None
        if c.date_of_birth:
            years = today.year - c.date_of_birth.year
            if (today.month, today.day) < (c.date_of_birth.month, c.date_of_birth.day):
                years -= 1
            age = max(0, years)

        if ben:
            ident = ben.rfid_id or c.registry_no or ""
            results.append({
                "id": ben.pk,
                "citizen_id": c.pk,
                "can_link": True,
                "name": name,
                "label": (
                    f"{ident or '—'} — {name}"
                    + (f" ({ben.beneficiary_class})" if ben.beneficiary_class else "")
                ),
                "registry_no": ident or c.registry_no or "",
                "barangay": c.barangay or ben.barangay or "",
                "sex": c.get_sex_display() if c.sex else "",
                "beneficiary_class": ben.beneficiary_class or "",
                "age": age,
            })
        else:
            results.append({
                "id": None,
                "citizen_id": c.pk,
                "can_link": False,
                "name": name,
                "label": f"{c.registry_no or '—'} — {name}",
                "registry_no": c.registry_no or "",
                "barangay": c.barangay or "",
                "sex": c.get_sex_display() if c.sex else "",
                "beneficiary_class": "",
                "age": age,
            })

    cache.set(cache_key, results, _CITIZEN_SEARCH_CACHE_TTL)
    return results


def enrolled_citizen_ids(exclude_beneficiary_pk=None):
    """Citizen PKs that already have a beneficiary record."""
    taken = Beneficiary.objects.exclude(citizen__isnull=True)
    if exclude_beneficiary_pk:
        taken = taken.exclude(pk=exclude_beneficiary_pk)
    return set(taken.values_list("citizen_id", flat=True))


def _citizen_pk_from_form(form):
    """Resolve the selected citizen PK from POST data, instance, or initial."""
    if form.is_bound:
        raw = form.data.get(form.add_prefix("citizen"), "")
        if str(raw).isdigit():
            return int(raw)
    if form.instance and form.instance.pk and form.instance.citizen_id:
        return form.instance.citizen_id
    initial = form.initial.get("citizen")
    if initial is not None:
        if hasattr(initial, "pk"):
            return initial.pk
        if str(initial).isdigit():
            return int(initial)
    return None


class BeneficiaryForm(forms.ModelForm):
    barangay = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "readonly": "readonly"}),
        label="Barangay",
    )
    # Visible locked field — mirrors Citizens “Monthly Income” (income_range display).
    # Numeric monthly_income stays hidden and is derived server-side from the citizen.
    # It is stored for reference only — qualification uses class + grant cooldown.
    income_range_display = forms.CharField(
        required=False,
        label="Monthly Income",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly",
            "placeholder": "From citizen registry…",
            "id": "id_income_range_display",
            "style": "background:#f8fafc;color:#0f172a;font-weight:600",
        }),
    )

    class Meta:
        model = Beneficiary
        fields = [
            "citizen",
            "last_name", "first_name", "middle_name", "sex",
            "beneficiary_class", "monthly_income",
            "contact_number", "address", "barangay",
            "municipality", "province", "rfid_id",
            "signature", "prior_grant_date", "is_active", "notes",
        ]
        widgets = {
            "citizen": forms.Select(attrs={"class": "form-select", "id": "id_citizen"}),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Dela Cruz",
                "readonly": "readonly",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Juan",
                "readonly": "readonly",
            }),
            "middle_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Santos (optional)",
                "readonly": "readonly",
            }),
            "sex": forms.Select(attrs={
                "class": "form-select",
                "style": "pointer-events:none;background:#f8fafc;color:#64748b",
                "tabindex": "-1",
            }),
            "beneficiary_class": forms.Select(attrs={
                "class": "form-select",
                "style": "pointer-events:none;background:#f8fafc;color:#64748b",
                "tabindex": "-1",
                "aria-readonly": "true",
            }),
            "monthly_income": forms.HiddenInput(attrs={
                "id": "id_monthly_income",
            }),
            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 09xx-xxx-xxxx",
                "readonly": "readonly",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "House/Lot No., Street Name",
                "readonly": "readonly",
            }),
            "municipality": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Bacnotan",
                "readonly": "readonly",
            }),
            "province": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. La Union",
                "readonly": "readonly",
            }),
            "rfid_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "From citizen registry",
                "readonly": "readonly",
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
        exclude_pk = self.instance.pk if self.instance and self.instance.pk else None
        if self.instance and self.instance.pk:
            current = self.instance.barangay or ""
        self.fields["barangay"].choices = get_barangay_choices(
            include_blank=True, include_name=current or None
        )
        # Do NOT load tens of thousands of <option>s — only the selected citizen.
        # Search uses AJAX (/beneficiaries/citizen-lookup/?q=…).
        selected_pk = _citizen_pk_from_form(self)
        if selected_pk:
            self.fields["citizen"].queryset = Citizen.objects.filter(pk=selected_pk)
        else:
            self.fields["citizen"].queryset = Citizen.objects.none()
        self.fields["citizen"].required = True
        self.fields["citizen"].empty_label = "— Search & select a citizen —"
        self.fields["citizen"].label = "Citizen (from registry)"
        self.fields["citizen"].help_text = (
            "Type at least 2 characters to search the registry. "
            "Only citizens not yet enrolled can be selected."
        )
        self.fields["citizen"].widget.attrs.update({
            "class": "form-select",
            "id": "id_citizen",
            "aria-label": "Selected citizen",
        })
        # HTML5 required on a hidden <select> is awkward; server still validates.
        self.fields["citizen"].widget.attrs.pop("required", None)
        self.fields["citizen"].label_from_instance = (
            lambda obj: f"{obj.registry_no or '—'} — {obj.last_name}, {obj.first_name}"
            + (f" {obj.middle_name}" if obj.middle_name else "")
        )
        self.fields["sex"].required = False
        # Class & income are locked from the citizen registry (server overrides POST).
        self.fields["beneficiary_class"].required = False
        self.fields["monthly_income"].required = False
        self.fields["beneficiary_class"].help_text = (
            "Filled automatically from the citizen’s vulnerable groups / occupation. "
            "Edit in Citizens — not changeable here."
        )
        self.fields["income_range_display"].help_text = (
            "Same Monthly Income as on the citizen’s registry record. "
            "Edit in Citizens — not changeable here."
        )
        # Prefill visible range from linked / selected citizen.
        citizen_for_display = None
        if selected_pk:
            citizen_for_display = (
                self.fields["citizen"].queryset.filter(pk=selected_pk).first()
            )
        if citizen_for_display and citizen_for_display.income_range:
            self.fields["income_range_display"].initial = (
                citizen_for_display.get_income_range_display()
            )
            _, monthly = eligibility_from_citizen(citizen_for_display)
            if monthly is not None and not self.is_bound:
                self.fields["monthly_income"].initial = monthly
        for name in (
            "last_name", "first_name", "middle_name", "contact_number",
            "address", "barangay", "municipality", "province", "rfid_id",
        ):
            self.fields[name].required = False

    def clean_citizen(self):
        citizen = self.cleaned_data.get("citizen")
        if not citizen:
            raise forms.ValidationError(
                "Select a citizen from the registry, or register a new citizen first."
            )
        qs = Beneficiary.objects.filter(citizen=citizen)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f"{citizen.full_name} is already enrolled as a beneficiary. "
                "Each citizen may only be enrolled once."
            )
        return citizen

    def clean(self):
        cleaned = super().clean()
        citizen = cleaned.get("citizen")
        if not citizen:
            return cleaned
        # Fill identity fields from citizen (readonly inputs may be omitted).
        cleaned["last_name"] = citizen.last_name
        cleaned["first_name"] = citizen.first_name
        cleaned["middle_name"] = citizen.middle_name or ""
        cleaned["sex"] = citizen.sex or ""
        cleaned["contact_number"] = citizen.contact_number or ""
        cleaned["address"] = citizen.address or ""
        cleaned["barangay"] = citizen.barangay or ""
        cleaned["municipality"] = citizen.municipality or ""
        cleaned["province"] = citizen.province or ""
        if citizen.rfid_tag:
            cleaned["rfid_id"] = citizen.rfid_tag
        elif not (cleaned.get("rfid_id") or getattr(self.instance, "rfid_id", None)):
            cleaned["rfid_id"] = citizen.registry_no or None
        else:
            cleaned["rfid_id"] = cleaned.get("rfid_id") or getattr(self.instance, "rfid_id", None) or None
        if cleaned.get("rfid_id") == "":
            cleaned["rfid_id"] = None
        if citizen.signature:
            cleaned["signature"] = citizen.signature

        # Security: always overwrite class / income from citizen — ignore client POST.
        ben_class, monthly = eligibility_from_citizen(citizen)
        if not ben_class:
            self.add_error(
                "beneficiary_class",
                "No beneficiary class found for this citizen. "
                "Set vulnerable groups or occupation on their Citizens record first.",
            )
        else:
            cleaned["beneficiary_class"] = ben_class
        if citizen.income_range:
            cleaned["income_range_display"] = citizen.get_income_range_display()
        else:
            cleaned["income_range_display"] = ""
        # Income is stored when available; it is not used for qualification.
        cleaned["monthly_income"] = monthly if monthly is not None else Decimal("0.00")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        citizen = self.cleaned_data.get("citizen") or instance.citizen
        if citizen:
            instance.sync_from_citizen(citizen)
        if commit:
            instance.save()
        return instance


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ["member", "relationship", "age"]
        widgets = {
            "member": forms.Select(attrs={
                "class": "form-select form-select-sm family-member-select",
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
        # Avoid loading every beneficiary into each row <select>.
        selected_pk = None
        if self.is_bound:
            raw = self.data.get(self.add_prefix("member"), "")
            if str(raw).isdigit():
                selected_pk = int(raw)
        elif self.instance and self.instance.member_id:
            selected_pk = self.instance.member_id

        if selected_pk:
            self.fields["member"].queryset = Beneficiary.objects.filter(pk=selected_pk)
        else:
            self.fields["member"].queryset = Beneficiary.objects.none()

        self.fields["member"].empty_label = "— Search beneficiary —"
        self.fields["member"].required = False
        self.fields["relationship"].required = False
        self.fields["member"].label_from_instance = (
            lambda obj: (
                f"{obj.rfid_id or '—'} — {obj.last_name}, {obj.first_name}"
                + (f" ({obj.beneficiary_class})" if obj.beneficiary_class else "")
            )
        )

    def clean(self):
        cleaned = super().clean()
        member = cleaned.get("member")
        relationship = cleaned.get("relationship")
        if cleaned.get("DELETE"):
            return cleaned
        if member and not relationship:
            self.add_error("relationship", "Select a relationship.")
        if relationship and not member:
            self.add_error("member", "Select a beneficiary.")
        return cleaned


FamilyMemberFormSet = inlineformset_factory(
    Beneficiary,
    FamilyMember,
    form=FamilyMemberForm,
    fk_name="beneficiary",
    extra=1,
    can_delete=True,
)


class BeneficiaryFingerprintForm(forms.ModelForm):
    class Meta:
        model = BeneficiaryFingerprint
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
        from citizens.fingerprint_match import normalize_template

        cleaned = super().clean()
        finger = cleaned.get("finger")
        template = normalize_template(cleaned.get("template_data"))
        image = (cleaned.get("image_data") or "").strip()
        device = (cleaned.get("device_name") or "").strip()

        # All 10 fingers are listed. Unused slots have a finger but no scan.
        if not template and not image:
            cleaned["template_data"] = template
            cleaned["image_data"] = image
            cleaned["device_name"] = device
            return cleaned
        if not finger:
            self.add_error("finger", "Select which finger was scanned.")
        cleaned["template_data"] = template
        cleaned["image_data"] = image
        cleaned["device_name"] = device
        return cleaned


class BaseBeneficiaryFingerprintFormSet(BaseInlineFormSet):
    def clean(self):
        from citizens.fingerprint_match import (
            DUPLICATE_THRESHOLD,
            hamming_hex,
            normalize_template,
        )

        super().clean()
        if any(self.errors):
            return
        seen_fingers = set()
        seen_templates = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            finger = form.cleaned_data.get("finger")
            template = normalize_template(form.cleaned_data.get("template_data"))
            image = (form.cleaned_data.get("image_data") or "").strip()
            if not template and not image:
                continue
            if finger in seen_fingers:
                form.add_error("finger", "This finger is already listed.")
            else:
                seen_fingers.add(finger)
            if template:
                for prev in seen_templates:
                    if hamming_hex(template, prev) <= DUPLICATE_THRESHOLD:
                        form.add_error(
                            "template_data",
                            "This fingerprint matches another finger on this form.",
                        )
                        break
                else:
                    seen_templates.append(template)

    def save_new_objects(self, commit=True):
        self.new_objects = []
        for form in self.extra_forms:
            if not form.has_changed():
                continue
            if self.can_delete and self._should_delete_form(form):
                continue
            template = (form.cleaned_data.get("template_data") or "").strip()
            image = (form.cleaned_data.get("image_data") or "").strip()
            if not template and not image:
                continue
            self.new_objects.append(self.save_new(form, commit=commit))
        return self.new_objects


def make_beneficiary_fingerprint_formset(data=None, instance=None, prefix="fp"):
    """List every finger. Duplicate scans are rejected against the whole database.

    When creating a new beneficiary linked to a citizen, biometrics live on the
    Citizen record — so we do not pre-render empty finger rows (extra=0).
    """
    fingers = [code for code, _label in BeneficiaryFingerprint.FINGER_CHOICES]
    enrolled = set()
    if instance is not None and getattr(instance, "pk", None):
        enrolled = set(instance.fingerprints.values_list("finger", flat=True))
    missing = [f for f in fingers if f not in enrolled]
    # On create (no instance pk): no empty finger rows — enroll uses citizen FPs.
    if instance is None or not getattr(instance, "pk", None):
        extra = 0 if data is None else 0
        initial = []
    else:
        extra = 0 if data is not None else len(missing)
        initial = [{"finger": f} for f in missing]
    FormSet = inlineformset_factory(
        Beneficiary,
        BeneficiaryFingerprint,
        form=BeneficiaryFingerprintForm,
        formset=BaseBeneficiaryFingerprintFormSet,
        fk_name="beneficiary",
        extra=extra,
        can_delete=True,
    )
    kwargs = {"prefix": prefix}
    if instance is not None:
        kwargs["instance"] = instance
    if data is None and initial:
        kwargs["initial"] = initial
    return FormSet(data, **kwargs)


BeneficiaryFingerprintFormSet = inlineformset_factory(
    Beneficiary,
    BeneficiaryFingerprint,
    form=BeneficiaryFingerprintForm,
    formset=BaseBeneficiaryFingerprintFormSet,
    fk_name="beneficiary",
    extra=0,
    can_delete=True,
)
