from django.urls import path

from . import views_workstations

urlpatterns = [
    path("", views_workstations.workstation_list, name="workstation-list"),
    path("<int:pk>/unblock/", views_workstations.workstation_unblock, name="workstation-unblock"),
]
