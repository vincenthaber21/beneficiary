from django.contrib import admin
from django.utils.html import format_html

from .models import AuditTrail


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "username_display",
        "action_badge",
        "module",
        "description_short",
        "ip_address",
        "success_badge",
    )
    list_filter = ("action", "module", "success", "created_at")
    search_fields = ("username", "description", "path", "ip_address", "module")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50
    readonly_fields = (
        "user",
        "username",
        "action",
        "module",
        "description",
        "path",
        "method",
        "ip_address",
        "user_agent",
        "success",
        "created_at",
    )
    fieldsets = (
        ("Event", {
            "fields": ("created_at", "action", "module", "description", "success"),
        }),
        ("User", {
            "fields": ("user", "username", "ip_address", "user_agent"),
        }),
        ("Request", {
            "fields": ("method", "path"),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Keep trails intact for security; only superusers may purge if needed.
        return request.user.is_superuser

    @admin.display(description="User", ordering="username")
    def username_display(self, obj):
        return obj.username or (obj.user.get_username() if obj.user else "—")

    @admin.display(description="Action", ordering="action")
    def action_badge(self, obj):
        colors = {
            AuditTrail.Action.LOGIN: "#166534",
            AuditTrail.Action.LOGOUT: "#334155",
            AuditTrail.Action.LOGIN_FAILED: "#991b1b",
            AuditTrail.Action.MODULE_OPEN: "#1d4ed8",
            AuditTrail.Action.CREATE: "#0f766e",
            AuditTrail.Action.UPDATE: "#a16207",
            AuditTrail.Action.DELETE: "#b91c1c",
            AuditTrail.Action.EXPORT: "#6d28d9",
            AuditTrail.Action.IMPORT: "#7c3aed",
            AuditTrail.Action.BACKUP: "#0369a1",
            AuditTrail.Action.RESTORE: "#c2410c",
        }
        color = colors.get(obj.action, "#475569")
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
            'background:{};color:#fff;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_action_display(),
        )

    @admin.display(description="Success", ordering="success", boolean=True)
    def success_badge(self, obj):
        return obj.success

    @admin.display(description="Description")
    def description_short(self, obj):
        if len(obj.description) > 80:
            return f"{obj.description[:80]}…"
        return obj.description
