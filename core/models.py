from django.conf import settings
from django.db import models


class AuditTrail(models.Model):
    """Immutable security log of user activity across the system."""

    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        LOGIN_FAILED = "login_failed", "Login failed"
        MODULE_OPEN = "module_open", "Opened module"
        CREATE = "create", "Created"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"
        VIEW = "view", "Viewed"
        EXPORT = "export", "Exported"
        IMPORT = "import", "Imported"
        BACKUP = "backup", "Backup"
        RESTORE = "restore", "Restore"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_trails",
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        help_text="Stored separately so the trail remains after a user is deleted.",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    module = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.CharField(max_length=500)
    path = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Trail"
        verbose_name_plural = "Audit Trails"
        indexes = [
            models.Index(fields=["-created_at", "action"]),
            models.Index(fields=["username", "-created_at"]),
        ]

    def __str__(self):
        who = self.username or (self.user.get_username() if self.user else "anonymous")
        return f"{self.created_at:%Y-%m-%d %H:%M} | {who} | {self.get_action_display()} | {self.module}"
