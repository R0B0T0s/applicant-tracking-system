from django.urls import path

from . import views

app_name = "hiring"

urlpatterns = [
    path("", views.home, name="home"),
    path("manager/", views.manager_tools, name="manager_tools"),
    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/new/", views.candidate_create, name="candidate_create"),
    path("candidates/<int:pk>/", views.candidate_detail, name="candidate_detail"),
    path("candidates/<int:pk>/edit/", views.candidate_edit, name="candidate_edit"),
    path(
        "candidates/<int:pk>/archive/",
        views.candidate_archive,
        name="candidate_archive",
    ),
    path(
        "candidates/<int:pk>/unarchive/",
        views.candidate_unarchive,
        name="candidate_unarchive",
    ),
]
