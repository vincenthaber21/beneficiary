from django.urls import path
from . import views

app_name = "programs"

urlpatterns = [
    path("", views.program_list, name="list"),
    path("add/", views.program_create, name="create"),
    path("<int:pk>/edit/", views.program_update, name="update"),
    path("<int:pk>/delete/", views.program_delete, name="delete"),
]
