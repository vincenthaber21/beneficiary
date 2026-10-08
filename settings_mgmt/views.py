from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from utils import admin_required, staff_required

from .backup import BackupError, build_backup_zip, restore_from_upload
from .models import SystemLogo, SystemSetting

DEFAULTS = [
    ("org_name", SystemLogo.DEFAULT_ORG_NAME, "Shown as the tagline on the login page"),
    ("org_address", "", "Organization address"),
    ("income_threshold", "15000", "Legacy monthly income threshold (Php) — not used in beneficiary qualification"),
    ("grant_cooldown_months", "3", "Default months before a beneficiary can receive another grant"),
    ("contact_email", "", "Contact email address"),
    ("contact_phone", "", "Contact phone number"),
]

CONFIRM_PHRASE = "RESTORE"


def ensure_defaults():
    for key, default, desc in DEFAULTS:
        SystemSetting.objects.get_or_create(key=key, defaults={"value": default, "description": desc})


@staff_required
def settings_view(request):
    ensure_defaults()
    settings = SystemSetting.objects.all()

    if request.method == "POST":
        for setting in settings:
            val = request.POST.get(f"setting_{setting.key}", "").strip()
            setting.value = val
            setting.save()

        # Keep SystemLogo branding in sync when org_name is edited here.
        org_name = request.POST.get("setting_org_name", "").strip()
        if org_name:
            logo = SystemLogo.load()
            if logo.org_name != org_name:
                logo.org_name = org_name
                # Avoid recursive SystemSetting.set from logo.save(); update field only.
                SystemLogo.objects.filter(pk=logo.pk).update(org_name=org_name)

        messages.success(request, "Settings saved successfully.")
        return redirect("settings_mgmt:settings")

    return render(request, "settings_mgmt/settings.html", {"settings": settings})


@admin_required
@require_http_methods(["GET", "POST"])
def backup_restore_view(request):
    """User-facing backup/restore page (administrators only)."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "backup":
            try:
                payload, filename = build_backup_zip()
            except BackupError as exc:
                messages.error(request, str(exc))
                return redirect("settings_mgmt:backup_restore")

            response = HttpResponse(payload, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "no-store"
            return response

        if action == "restore":
            uploaded = request.FILES.get("backup_file")
            confirm = (request.POST.get("confirm_phrase") or "").strip()

            if confirm != CONFIRM_PHRASE:
                messages.error(
                    request,
                    f"Type {CONFIRM_PHRASE} exactly to confirm restore.",
                )
                return redirect("settings_mgmt:backup_restore")

            if not uploaded:
                messages.error(request, "Choose a backup file to restore.")
                return redirect("settings_mgmt:backup_restore")

            try:
                result = restore_from_upload(uploaded)
            except BackupError as exc:
                messages.error(request, str(exc))
                return redirect("settings_mgmt:backup_restore")

            media_n = result.get("media_files_restored", 0)
            messages.success(
                request,
                "Data restored successfully. Database replaced"
                + (f" and {media_n} media file(s) restored." if media_n else "."),
            )
            return redirect("settings_mgmt:backup_restore")

        messages.error(request, "Unknown action.")
        return redirect("settings_mgmt:backup_restore")

    return render(
        request,
        "settings_mgmt/backup_restore.html",
        {"confirm_phrase": CONFIRM_PHRASE},
    )
