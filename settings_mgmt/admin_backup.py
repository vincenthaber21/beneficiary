"""Django admin views for secure data backup and restore."""
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.views.decorators.http import require_http_methods

from .backup import BackupError, build_backup_zip, restore_from_upload

CONFIRM_PHRASE = "RESTORE"


def _require_superuser(request):
    if not request.user.is_active or not request.user.is_superuser:
        raise PermissionDenied("Only superusers can backup or restore data.")


@staff_member_required
@require_http_methods(["GET", "POST"])
def backup_restore_view(request):
    _require_superuser(request)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "backup":
            try:
                payload, filename = build_backup_zip()
            except BackupError as exc:
                messages.error(request, str(exc))
                return redirect("admin:backup_restore")

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
                return redirect("admin:backup_restore")

            if not uploaded:
                messages.error(request, "Choose a backup file to restore.")
                return redirect("admin:backup_restore")

            try:
                result = restore_from_upload(uploaded)
            except BackupError as exc:
                messages.error(request, str(exc))
                return redirect("admin:backup_restore")

            media_n = result.get("media_files_restored", 0)
            messages.success(
                request,
                "Data restored successfully. "
                f"Database replaced"
                + (f" and {media_n} media file(s) restored." if media_n else "."),
            )
            return redirect("admin:backup_restore")

        messages.error(request, "Unknown action.")
        return redirect("admin:backup_restore")

    context = {
        **admin.site.each_context(request),
        "title": "Backup & Restore",
        "confirm_phrase": CONFIRM_PHRASE,
    }
    return render(request, "admin/backup_restore.html", context)


def _patch_admin_urls():
    """Attach backup/restore routes to the default admin site (once)."""
    if getattr(admin.site, "_ebahagi_backup_urls_patched", False):
        return

    original_get_urls = admin.site.get_urls

    def get_urls():
        custom = [
            path(
                "backup-restore/",
                admin.site.admin_view(backup_restore_view),
                name="backup_restore",
            ),
        ]
        return custom + original_get_urls()

    admin.site.get_urls = get_urls
    admin.site._ebahagi_backup_urls_patched = True


_patch_admin_urls()
