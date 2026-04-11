from django.urls import path

from . import views_sudo

urlpatterns = [
    path("acquire/", views_sudo.sudo_acquire, name="sudo-acquire"),
    path("status/", views_sudo.sudo_status, name="sudo-status"),
    path("release/", views_sudo.sudo_release, name="sudo-release"),
]
