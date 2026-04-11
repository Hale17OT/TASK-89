"""Audit URL configuration."""
from django.urls import path

from . import views

urlpatterns = [
    path("entries/", views.audit_list, name="audit-list"),
    path("entries/<int:pk>/", views.audit_detail, name="audit-detail"),
    path("verify-chain/", views.audit_verify_chain, name="audit-verify-chain"),
    path("purge/", views.audit_purge, name="audit-purge"),
]
