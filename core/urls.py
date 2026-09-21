from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("audit-trails/", views.audit_trails, name="audit_trails"),
    path("fingerprint-check/", views.fingerprint_check, name="fingerprint_check"),
]
