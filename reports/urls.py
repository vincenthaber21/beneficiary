from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_index, name="index"),
    path("import/excel/", views.import_from_excel, name="import_excel"),
    path("export/beneficiaries/", views.export_beneficiaries, name="export_beneficiaries"),
    path("export/records/", views.export_records, name="export_records"),
]
