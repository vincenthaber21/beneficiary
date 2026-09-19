from django.urls import path
from . import views

app_name = "user_mgmt"

urlpatterns = [
    path("", views.user_list, name="list"),
    path("add/", views.user_create, name="create"),
    path("<int:pk>/edit/", views.user_update, name="update"),
    path("<int:pk>/delete/", views.user_delete, name="delete"),
]
