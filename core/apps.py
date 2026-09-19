from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core / Security"

    def ready(self):
        # Register auth signal handlers for login / logout audit logging.
        from . import signals  # noqa: F401
