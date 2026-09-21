from django.urls import path

from . import views

app_name = "citizens"

urlpatterns = [
    path("", views.citizen_list, name="list"),
    path("add/", views.citizen_create, name="create"),
    path("search/", views.citizen_search, name="search"),
    path("id-cards/", views.citizen_id_cards_all, name="id_cards_all"),
    path("<int:pk>/", views.citizen_detail, name="detail"),
    path("<int:pk>/edit/", views.citizen_update, name="update"),
    path("<int:pk>/id-card/", views.citizen_id_card, name="id_card"),
    path("<int:pk>/generate-id/", views.generate_id, name="generate_id"),
    path("<int:pk>/delete/", views.citizen_delete, name="delete"),
]
