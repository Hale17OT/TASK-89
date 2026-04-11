"""URL patterns for bulk export endpoints."""
from django.urls import path

from . import views_export

urlpatterns = [
    path("patients/", views_export.bulk_export_patients, name="export-patients"),
    path("media/", views_export.bulk_export_media, name="export-media"),
    path("financials/", views_export.bulk_export_financials, name="export-financials"),
]
