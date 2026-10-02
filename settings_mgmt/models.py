from django.core.files.base import ContentFile
from django.db import models

from .image_utils import remove_solid_background


def system_logo_upload_path(instance, filename):
    return f"system/logo/{filename}"


class SystemLogo(models.Model):
    DEFAULT_ORG_NAME = "Humanitarian Assistance Grant Management"

    logo = models.ImageField(upload_to=system_logo_upload_path, blank=True, null=True)
    org_name = models.CharField(
        max_length=200,
        blank=True,
        default=DEFAULT_ORG_NAME,
        verbose_name="Feature / organization name",
        help_text="Shown under the logo on the login page, header, and dashboard. Easy to change anytime.",
    )
    alt_text = models.CharField(max_length=100, blank=True, default="Organization logo")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Branding"
        verbose_name_plural = "System Branding"

    def __str__(self):
        return self.org_name or "System Branding"

    def save(self, *args, **kwargs):
        if self.logo and not getattr(self.logo, "_committed", True):
            processed = remove_solid_background(self.logo)
            self.logo.save("logo.png", ContentFile(processed.read()), save=False)

        if not (self.org_name or "").strip():
            self.org_name = self.DEFAULT_ORG_NAME

        self.pk = 1
        super().save(*args, **kwargs)

        # Keep SystemSetting.org_name in sync for the settings page.
        SystemSetting.set(
            "org_name",
            self.org_name,
            description="Shown as the tagline on the login page",
        )

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def has_logo(self):
        return bool(self.logo)


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=""):
        obj, _ = cls.objects.get_or_create(key=key)
        obj.value = value
        if description:
            obj.description = description
        obj.save()
        return obj
