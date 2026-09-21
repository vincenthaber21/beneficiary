from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core / Security"

    def ready(self):
        # Register auth signal handlers for login / logout audit logging.
        from . import signals  # noqa: F401

        # Start fingerprint_bridge with runserver (single process on :8765).
        from .fingerprint_bridge import ensure_fingerprint_bridge

        ensure_fingerprint_bridge()
