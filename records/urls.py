from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("", views.record_list, name="list"),
    path("add/", views.record_create, name="create"),
    path("<int:pk>/edit/", views.record_update, name="update"),
    path("<int:pk>/delete/", views.record_delete, name="delete"),
]
