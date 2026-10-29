from django.urls import path

from . import views

app_name = "hiring"

urlpatterns = [
    path("", views.home, name="home"),
    path("manager/", views.manager_tools, name="manager_tools"),
]
