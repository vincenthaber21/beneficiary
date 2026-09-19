from django.contrib import admin
from django.utils.html import format_html

from . import admin_backup  # noqa: F401  — registers backup/restore admin URLs
from .models import SystemLogo, SystemSetting

admin.site.site_header = "e-BAHAGI Administration"
admin.site.site_title = "e-BAHAGI Admin"
admin.site.index_title = "System administration"


@admin.register(SystemLogo)
class SystemLogoAdmin(admin.ModelAdmin):
    fields = ("logo", "logo_preview", "alt_text", "updated_at")
    readonly_fields = ("logo_preview", "updated_at")

    def has_add_permission(self, request):
        return not SystemLogo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Preview")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<div style="display:inline-block;padding:10px;border-radius:8px;border:1px solid #e2e8f0;'
                'background:repeating-conic-gradient(#e2e8f0 0% 25%,#fff 0% 50%) 50%/16px 16px;">'
                '<img src="{}" style="max-height:80px;max-width:220px;display:block;" />'
                "</div>",
                obj.logo.url,
            )
        return "No logo uploaded yet."


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value_preview", "description", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("key", "value", "description")
    readonly_fields = ("updated_at",)
    ordering = ("key",)
    fieldsets = (
        (None, {"fields": ("key", "value", "description")}),
        ("Metadata", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    @admin.display(description="Value")
    def value_preview(self, obj):
        if len(obj.value) > 60:
            return f"{obj.value[:60]}…"
        return obj.value
