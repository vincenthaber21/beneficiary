from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create a default admin user (admin/admin123) if no superuser exists."

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            user = User.objects.create_superuser(
                username="admin",
                email="admin@ebahagi.local",
                password="admin123",
                first_name="System",
                last_name="Administrator",
            )
            # Create profile
            try:
                from user_mgmt.models import UserProfile
                UserProfile.objects.get_or_create(user=user, defaults={"role": "admin"})
            except Exception:
                pass
            self.stdout.write(self.style.SUCCESS("Default admin created: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists — skipping.")
