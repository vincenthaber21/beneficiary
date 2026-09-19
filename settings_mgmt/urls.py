from django.urls import path
from . import views

app_name = "settings_mgmt"

urlpatterns = [
    path("", views.settings_view, name="settings"),
    path("backup-restore/", views.backup_restore_view, name="backup_restore"),
]
