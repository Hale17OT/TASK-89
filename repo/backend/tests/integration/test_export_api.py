"""Integration tests for the /api/v1/export/ bulk export endpoints."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(username="export_admin", password="TestPass123!", role="admin", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-export-test"
    # Also login to establish a session (needed for sudo token persistence)
    client.login(username="export_admin", password="TestPass123!")
    return client


@pytest.fixture
def frontdesk_client(db):
    user = User.objects.create_user(username="export_fd", password="TestPass123!", role="front_desk")
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-export-test-fd"
    return client


def _acquire_sudo(client, password="TestPass123!"):
    """Acquire a sudo token for bulk_export."""
    resp = client.post("/api/v1/sudo/acquire/", {
        "password": password,
        "action_class": "bulk_export",
    }, format="json")
    return resp


class TestBulkExportPatients:
    def test_export_patients_requires_auth(self, db):
        client = APIClient()
        resp = client.post("/api/v1/export/patients/")
        assert resp.status_code in (401, 403)

    def test_export_patients_requires_admin(self, frontdesk_client):
        resp = frontdesk_client.post("/api/v1/export/patients/")
        assert resp.status_code == 403

    def test_export_patients_requires_sudo(self, admin_client):
        """Admin without sudo token gets 403."""
        resp = admin_client.post("/api/v1/export/patients/", {"confirm": True}, format="json")
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_export_patients_success_with_sudo(self, admin_client):
        _acquire_sudo(admin_client)
        resp = admin_client.post("/api/v1/export/patients/", {"confirm": True}, format="json")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        content = resp.content.decode("utf-8")
        assert "id" in content
        assert "mrn_masked" in content


class TestBulkExportMedia:
    @pytest.mark.django_db
    def test_export_media_success_with_sudo(self, admin_client):
        _acquire_sudo(admin_client)
        resp = admin_client.post("/api/v1/export/media/", {"confirm": True}, format="json")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_export_media_non_admin_forbidden(self, frontdesk_client):
        resp = frontdesk_client.post("/api/v1/export/media/")
        assert resp.status_code == 403


class TestBulkExportFinancials:
    @pytest.mark.django_db
    def test_export_financials_success_with_sudo(self, admin_client):
        _acquire_sudo(admin_client)
        resp = admin_client.post("/api/v1/export/financials/", {"confirm": True}, format="json")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_export_financials_non_admin_forbidden(self, frontdesk_client):
        resp = frontdesk_client.post("/api/v1/export/financials/")
        assert resp.status_code == 403
