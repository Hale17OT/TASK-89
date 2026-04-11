"""MedRights URL Configuration."""
from django.urls import include, path

urlpatterns = [
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/patients/", include("apps.mpi.urls")),
    path("api/v1/patients/<uuid:patient_id>/consents/", include("apps.consent.urls")),
    path("api/v1/media/", include("apps.media_engine.urls")),
    path("api/v1/financials/", include("apps.financials.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/sudo/", include("apps.accounts.urls_sudo")),
    path("api/v1/users/", include("apps.accounts.urls_users")),
    path("api/v1/workstations/", include("apps.accounts.urls_workstations")),
    path("api/v1/logs/", include("apps.audit.urls_client_logs")),
    path("api/v1/export/", include("apps.accounts.urls_export")),
    path("api/v1/policies/", include("apps.accounts.urls_policy")),
]
