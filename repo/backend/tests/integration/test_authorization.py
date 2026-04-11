"""Authorization boundary tests: verify 401/403 for unauthorized access."""
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestUnauthenticatedDenial:
    """Verify all protected endpoints reject unauthenticated requests."""

    PROTECTED_GETS = [
        "/api/v1/patients/?q=test",
        "/api/v1/media/",
        "/api/v1/financials/orders/",
        "/api/v1/reports/subscriptions/",
        "/api/v1/reports/outbox/",
        "/api/v1/reports/dashboard/",
        "/api/v1/audit/entries/",
        "/api/v1/users/",
    ]

    @pytest.mark.parametrize("url", PROTECTED_GETS)
    def test_unauthenticated_get_rejected(self, url):
        client = APIClient()
        resp = client.get(url)
        assert resp.status_code in (401, 403)

    PROTECTED_POSTS = [
        "/api/v1/patients/create/",
        "/api/v1/media/upload/",
        "/api/v1/financials/orders/",
        "/api/v1/media/infringement/",
    ]

    @pytest.mark.parametrize("url", PROTECTED_POSTS)
    def test_unauthenticated_post_rejected(self, url):
        client = APIClient()
        resp = client.post(url, {})
        assert resp.status_code in (401, 403)


class TestRoleDenial:
    """Verify role boundaries are enforced."""

    def test_clinician_cannot_create_patient(self, clinician_client):
        resp = clinician_client.post("/api/v1/patients/create/", {
            "mrn": "X001", "first_name": "A", "last_name": "B",
            "date_of_birth": "1990-01-01", "gender": "M",
        }, format="json")
        assert resp.status_code == 403

    def test_frontdesk_cannot_access_infringements(self, frontdesk_client):
        resp = frontdesk_client.get("/api/v1/media/infringement/")
        assert resp.status_code == 403

    def test_frontdesk_cannot_access_audit(self, frontdesk_client):
        resp = frontdesk_client.get("/api/v1/audit/entries/")
        assert resp.status_code == 403

    def test_clinician_cannot_create_order(self, clinician_client):
        resp = clinician_client.post("/api/v1/financials/orders/", {}, format="json")
        assert resp.status_code == 403

    def test_frontdesk_cannot_access_reports(self, frontdesk_client):
        resp = frontdesk_client.get("/api/v1/reports/subscriptions/")
        assert resp.status_code == 403

    def test_compliance_cannot_create_patient(self, compliance_client):
        resp = compliance_client.post("/api/v1/patients/create/", {}, format="json")
        assert resp.status_code == 403

    def test_frontdesk_cannot_disable_user(self, frontdesk_client):
        resp = frontdesk_client.post("/api/v1/users/00000000-0000-0000-0000-000000000000/disable/", {})
        assert resp.status_code == 403

    def test_clinician_cannot_export(self, clinician_client):
        resp = clinician_client.post("/api/v1/export/patients/")
        assert resp.status_code == 403
