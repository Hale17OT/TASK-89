"""Integration tests for the Reports & Outbox API endpoints.

Tests verify:
- Subscription CRUD requires compliance/admin role
- Outbox list/detail/download requires compliance/admin
- Dashboard requires compliance/admin
- Non-privileged roles (front_desk, clinician) are rejected with 403
"""
import pytest

from apps.reports.models import OutboxItem, ReportSubscription


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Subscriptions - Access Control
# ------------------------------------------------------------------

class TestCreateSubscription:
    def test_admin_creates_subscription(self, auth_client):
        resp = auth_client.post(
            "/api/v1/reports/subscriptions/",
            {
                "name": "Daily Recon Report",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "run_time": "23:00:00",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["name"] == "Daily Recon Report"

    def test_non_admin_creating_subscription_returns_403(self, compliance_client):
        """Compliance can list but NOT create."""
        resp = compliance_client.post(
            "/api/v1/reports/subscriptions/",
            {
                "name": "Sneaky",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "run_time": "12:00:00",
            },
            format="json",
        )
        assert resp.status_code == 403


class TestListSubscriptions:
    def test_compliance_can_list(self, compliance_client, auth_client):
        """Compliance role can list subscriptions."""
        auth_client.post(
            "/api/v1/reports/subscriptions/",
            {
                "name": "Test Sub",
                "report_type": "consent_expiry",
                "schedule": "weekly",
                "output_format": "excel",
                "run_time": "08:00:00",
                "run_day_of_week": 0,
            },
            format="json",
        )
        resp = compliance_client.get("/api/v1/reports/subscriptions/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert resp.data["count"] >= 1

    def test_frontdesk_cannot_list_subscriptions(self, frontdesk_client):
        """Front desk role is denied access to subscriptions."""
        resp = frontdesk_client.get("/api/v1/reports/subscriptions/")
        assert resp.status_code == 403

    def test_clinician_cannot_list_subscriptions(self, clinician_client):
        """Clinician role is denied access to subscriptions."""
        resp = clinician_client.get("/api/v1/reports/subscriptions/")
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Outbox - Access Control
# ------------------------------------------------------------------

class TestOutboxAccessControl:
    def test_admin_can_access_outbox(self, auth_client):
        resp = auth_client.get("/api/v1/reports/outbox/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "results" in resp.data

    def test_compliance_can_access_outbox(self, compliance_client):
        resp = compliance_client.get("/api/v1/reports/outbox/")
        assert resp.status_code == 200

    def test_frontdesk_cannot_access_outbox(self, frontdesk_client):
        resp = frontdesk_client.get("/api/v1/reports/outbox/")
        assert resp.status_code == 403

    def test_clinician_cannot_access_outbox(self, clinician_client):
        resp = clinician_client.get("/api/v1/reports/outbox/")
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Dashboard - Access Control
# ------------------------------------------------------------------

class TestReportDashboard:
    def test_admin_sees_dashboard(self, auth_client):
        resp = auth_client.get("/api/v1/reports/dashboard/")
        assert resp.status_code == 200
        assert "queued" in resp.data
        assert "delivered" in resp.data
        assert "failed" in resp.data
        assert "generating" in resp.data
        assert "stalled" in resp.data
        assert "recent" in resp.data

    def test_compliance_sees_dashboard(self, compliance_client):
        resp = compliance_client.get("/api/v1/reports/dashboard/")
        assert resp.status_code == 200

    def test_frontdesk_cannot_see_dashboard(self, frontdesk_client):
        resp = frontdesk_client.get("/api/v1/reports/dashboard/")
        assert resp.status_code == 403
