from django.urls import path
from . import views

app_name = "beneficiaries"

urlpatterns = [
    path("", views.beneficiary_list, name="list"),
    path("add/", views.beneficiary_create, name="create"),
    path("auto-enroll/", views.beneficiary_auto_enroll, name="auto_enroll"),
    path("search/", views.beneficiary_search, name="search"),
    path("citizen-lookup/", views.citizen_lookup, name="citizen_lookup"),
    path("export/excel/", views.beneficiary_export_excel, name="export_excel"),
    path("id-cards/", views.beneficiary_id_cards_all, name="id_cards_all"),
    path("<int:pk>/", views.beneficiary_detail, name="detail"),
    path("<int:pk>/edit/", views.beneficiary_update, name="update"),
    path("<int:pk>/id-card/", views.beneficiary_id_card, name="id_card"),
    path("<int:pk>/generate-id/", views.generate_id, name="generate_id"),
    path("<int:pk>/delete/", views.beneficiary_delete, name="delete"),
    path("rfid/", views.rfid_check, name="rfid"),
]
