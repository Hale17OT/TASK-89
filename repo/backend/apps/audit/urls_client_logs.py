"""URL for client-side error logging endpoint."""
from django.urls import path

from . import views_client_logs

urlpatterns = [
    path("client-errors/", views_client_logs.client_error_log, name="client-error-log"),
]
