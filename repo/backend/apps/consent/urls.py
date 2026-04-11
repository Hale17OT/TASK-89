"""Consent URL configuration.

These URLs are included under /api/v1/patients/<uuid:patient_id>/consents/
by the root URL conf, so paths here are relative to that prefix.
"""
from django.urls import path

from . import views

urlpatterns = [
    # GET  .../consents/       -- list
    # POST .../consents/       -- create
    path("", views.consent_list_create, name="consent-list-create"),

    # GET .../consents/<uuid>/  -- detail
    path("<uuid:pk>/", views.consent_detail, name="consent-detail"),

    # POST .../consents/<uuid>/revoke/  -- revoke
    path("<uuid:pk>/revoke/", views.consent_revoke, name="consent-revoke"),
]
