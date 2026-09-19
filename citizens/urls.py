from django.urls import path

from . import views

app_name = "citizens"

urlpatterns = [
    path("", views.citizen_list, name="list"),
    path("add/", views.citizen_create, name="create"),
    path("<int:pk>/", views.citizen_detail, name="detail"),
    path("<int:pk>/edit/", views.citizen_update, name="update"),
    path("<int:pk>/id-card/", views.citizen_id_card, name="id_card"),
    path("<int:pk>/delete/", views.citizen_delete, name="delete"),
]
