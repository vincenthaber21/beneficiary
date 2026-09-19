from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("core.urls", namespace="core")),
    path("programs/", include("programs.urls", namespace="programs")),
    path("beneficiaries/", include("beneficiaries.urls", namespace="beneficiaries")),
    path("citizens/", include("citizens.urls", namespace="citizens")),
    path("records/", include("records.urls", namespace="records")),
    path("reports/", include("reports.urls", namespace="reports")),
    path("users/", include("user_mgmt.urls", namespace="user_mgmt")),
    path("settings/", include("settings_mgmt.urls", namespace="settings_mgmt")),
    # Legacy checker
    path("check/", include("checker.urls", namespace="checker")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
