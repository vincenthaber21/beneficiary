from django import forms
from django.contrib import admin

from .models import (
    Barangay,
    Citizen,
    CitizenFamilyMember,
    CitizenFingerprint,
    get_barangay_choices,
)


class CitizenFamilyMemberInline(admin.TabularInline):
    model = CitizenFamilyMember
    fk_name = "citizen"
    extra = 1
    autocomplete_fields = ("member",)
    fields = ("member", "full_name", "relationship")


class CitizenFingerprintInline(admin.TabularInline):
    model = CitizenFingerprint
    extra = 1
    fields = (
        "finger",
        "template_data",
        "quality",
        "device_name",
        "is_primary",
        "registered_at",
    )
    readonly_fields = ("registered_at",)


class CitizenAdminForm(forms.ModelForm):
    class Meta:
        model = Citizen
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = ""
        if self.instance and self.instance.pk:
            current = self.instance.barangay or ""
        self.fields["barangay"] = forms.ChoiceField(
            choices=get_barangay_choices(include_blank=True, include_name=current or None),
            required=False,
            label="Barangay",
            help_text=(
                "Select a barangay. To add a new one, go to "
                "Citizen Registry → Barangays → Add barangay."
            ),
        )


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ("name", "population", "is_active", "updated_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
    list_editable = ("population", "is_active")
    list_per_page = 50
    fields = ("name", "population", "is_active")


@admin.register(CitizenFingerprint)
class CitizenFingerprintAdmin(admin.ModelAdmin):
    list_display = (
        "citizen",
        "finger",
        "is_primary",
        "quality",
        "device_name",
        "registered_at",
    )
    list_filter = ("finger", "is_primary", "registered_at")
    search_fields = (
        "citizen__registry_no",
        "citizen__last_name",
        "citizen__first_name",
        "template_data",
        "device_name",
    )
    autocomplete_fields = ("citizen",)
    readonly_fields = ("registered_at", "updated_at")


@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    form = CitizenAdminForm
    list_display = (
        "registry_no",
        "last_name",
        "first_name",
        "middle_name",
        "sex",
        "date_of_birth",
        "barangay",
        "municipality",
        "income_range",
        "status",
        "date_registered",
    )
    list_filter = (
        "status",
        "sex",
        "civil_status",
        "education",
        "income_range",
        "barangay",
        "municipality",
        "province",
        "date_registered",
    )
    search_fields = (
        "registry_no",
        "last_name",
        "first_name",
        "middle_name",
        "philsys_id",
        "voter_id",
        "contact_number",
        "rfid_tag",
        "barangay",
        "municipality",
        "other_id_number",
    )
    list_per_page = 50
    date_hierarchy = "date_registered"
    ordering = ("last_name", "first_name")
    readonly_fields = ("registry_no", "date_registered", "created_at", "updated_at")
    inlines = [CitizenFamilyMemberInline, CitizenFingerprintInline]

    fieldsets = (
        ("Personal Information", {
            "fields": (
                "registry_no",
                ("last_name", "first_name"),
                ("middle_name", "suffix"),
                ("date_of_birth", "sex"),
                ("civil_status", "religion"),
                ("education", "contact_number"),
                "rfid_tag",
            ),
        }),
        ("Current Address", {
            "fields": (
                "address",
                ("barangay", "municipality"),
                ("province", "zip_code"),
            ),
            "description": (
                "Barangay is a dropdown. Add or edit barangays under "
                "Citizen Registry → Barangays."
            ),
        }),
        ("Work Information", {
            "fields": (
                "income_range",
                ("occupation_1", "occupation_2", "occupation_3"),
            ),
        }),
        ("Vulnerable Group & Health", {
            "fields": ("vulnerable_groups", "health_conditions"),
        }),
        ("Government IDs", {
            "fields": (
                "philsys_id",
                "voter_id",
                ("other_id_type", "other_id_number"),
            ),
        }),
        ("Other", {
            "fields": (
                "place_of_birth",
                "email",
                "attachment",
                "signature",
                "status",
                "notes",
                "date_registered",
                "created_at",
                "updated_at",
            ),
        }),
    )
