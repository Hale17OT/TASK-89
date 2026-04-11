"""MPI URL configuration."""
from django.urls import path

from . import views

urlpatterns = [
    # GET  /api/v1/patients/?q=<term>  -- search
    # POST /api/v1/patients/           -- create
    path("", views.patient_search, name="patient-search"),
    path("create/", views.patient_create, name="patient-create"),

    # GET   /api/v1/patients/<uuid>/       -- detail (masked)
    # PATCH /api/v1/patients/<uuid>/       -- update
    path("<uuid:pk>/", views.patient_detail, name="patient-detail"),
    path("<uuid:pk>/update/", views.patient_update, name="patient-update"),

    # POST /api/v1/patients/<uuid>/break-glass/
    path("<uuid:pk>/break-glass/", views.break_glass, name="patient-break-glass"),
]
