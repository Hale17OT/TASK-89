"""Integration tests for admin-level API endpoints (users, workstations, audit)."""
import pytest

from apps.accounts.models import User, WorkstationBlacklist


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# User disable requires sudo
# ------------------------------------------------------------------

class TestUserDisableRequiresSudo:
    def test_disable_without_sudo_returns_403(self, auth_client, frontdesk_user):
        """POST disable without sudo returns 403."""
        resp = auth_client.post(
            f"/api/v1/users/{frontdesk_user.pk}/disable/",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "sudo_required"


# ------------------------------------------------------------------
# User list - admin only
# ------------------------------------------------------------------

class TestUserListAdminOnly:
    def test_non_admin_gets_403(self, frontdesk_client):
        """Non-admin gets 403 on user list."""
        resp = frontdesk_client.get("/api/v1/users/")
        assert resp.status_code == 403

    def test_admin_can_list(self, auth_client):
        """Admin can access user list."""
        resp = auth_client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "results" in resp.data


# ------------------------------------------------------------------
# Workstation unblock requires sudo
# ------------------------------------------------------------------

class TestWorkstationUnblockRequiresSudo:
    def test_unblock_without_sudo_returns_403(self, auth_client, admin_user):
        """POST unblock without sudo returns 403."""
        # Create a blacklisted workstation entry
        entry = WorkstationBlacklist.objects.create(
            client_ip="10.0.0.99",
            workstation_id="ws-blocked-001",
            lockout_count=5,
            is_active=True,
        )

        resp = auth_client.post(
            f"/api/v1/workstations/{entry.pk}/unblock/",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "sudo_required"


# ------------------------------------------------------------------
# Audit list - admin or compliance
# ------------------------------------------------------------------

class TestAuditListAdminOrCompliance:
    def test_admin_can_access(self, auth_client):
        """Admin can access audit list."""
        resp = auth_client.get("/api/v1/audit/entries/")
        assert resp.status_code == 200
        assert "count" in resp.data

    def test_frontdesk_gets_403(self, frontdesk_client):
        """Front desk user gets 403."""
        resp = frontdesk_client.get("/api/v1/audit/entries/")
        assert resp.status_code == 403

    def test_compliance_can_access(self, compliance_client):
        """Compliance user can access audit list."""
        resp = compliance_client.get("/api/v1/audit/entries/")
        assert resp.status_code == 200
        assert "count" in resp.data


# ------------------------------------------------------------------
# Audit verify chain
# ------------------------------------------------------------------

class TestAuditVerifyChain:
    def test_admin_can_verify_chain(self, auth_client):
        """Admin can verify audit chain."""
        resp = auth_client.post("/api/v1/audit/verify-chain/")
        assert resp.status_code == 200
        assert "is_valid" in resp.data
        assert "total_checked" in resp.data
