"""Integration tests for the authentication API endpoints."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import LoginAttempt, User


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _login(client, username="admin_user", password="AdminPass123!",
           workstation="ws-001"):
    return client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        format="json",
        HTTP_X_WORKSTATION_ID=workstation,
    )


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, admin_user):
        client = APIClient()
        resp = _login(client)
        assert resp.status_code == 200
        assert resp.data["user"]["username"] == "admin_user"
        assert resp.data["user"]["role"] == "admin"
        assert "idle_timeout_seconds" in resp.data

    def test_login_invalid_password(self, admin_user):
        client = APIClient()
        resp = _login(client, password="WrongPassword!")
        assert resp.status_code == 401
        assert resp.data["error"] == "invalid_credentials"

    def test_login_missing_workstation_id(self, admin_user):
        """The throttle middleware rejects login without X-Workstation-ID."""
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"username": "admin_user", "password": "AdminPass123!"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "workstation_id_required"

    def test_login_throttle(self, admin_user):
        """After 5 failed attempts the 6th is rejected with 429."""
        client = APIClient()
        for _ in range(5):
            _login(client, password="bad")

        resp = _login(client, password="bad")
        assert resp.status_code == 429

    def test_single_lockout_per_window(self, admin_user):
        """A burst of failures beyond 5 creates only ONE lockout record."""
        from apps.accounts.models import Lockout
        client = APIClient()
        # Fire 10 failures (all within the same lockout window)
        for _ in range(10):
            _login(client, password="bad")
        lockouts = Lockout.objects.filter(
            client_ip="127.0.0.1", workstation_id="ws-001"
        )
        assert lockouts.count() == 1, (
            f"Expected 1 lockout but found {lockouts.count()}"
        )

    def test_blacklist_requires_distinct_lockout_windows(self, admin_user):
        """Blacklist triggers only after 3 distinct lockout windows, not from one burst."""
        from apps.accounts.models import Lockout, WorkstationBlacklist
        client = APIClient()
        # Single burst should NOT blacklist (only 1 lockout record)
        for _ in range(10):
            _login(client, password="bad")
        blacklisted = WorkstationBlacklist.objects.filter(
            client_ip="127.0.0.1", workstation_id="ws-001", is_active=True
        ).exists()
        assert not blacklisted, "Single burst should not trigger blacklist"


# ------------------------------------------------------------------
# Logout
# ------------------------------------------------------------------

class TestLogout:
    def test_logout(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post("/api/v1/auth/logout/", HTTP_X_WORKSTATION_ID="ws-001")
        assert resp.status_code == 204


# ------------------------------------------------------------------
# Session
# ------------------------------------------------------------------

class TestSession:
    def test_session_info(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.get("/api/v1/auth/session/", HTTP_X_WORKSTATION_ID="ws-001")
        assert resp.status_code == 200
        assert resp.data["user"]["username"] == "admin_user"
        assert "idle_remaining_seconds" in resp.data

    def test_session_info_unauthenticated(self):
        client = APIClient()
        resp = client.get("/api/v1/auth/session/", HTTP_X_WORKSTATION_ID="ws-001")
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Change password
# ------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_success(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post(
            "/api/v1/auth/change-password/",
            {
                "current_password": "AdminPass123!",
                "new_password": "NewSecurePass999!",
            },
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 200

        # Old password should no longer work
        client2 = APIClient()
        resp2 = _login(client2, password="AdminPass123!")
        assert resp2.status_code == 401

        # New password should work
        resp3 = _login(client2, password="NewSecurePass999!")
        assert resp3.status_code == 200

    def test_change_password_wrong_current(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post(
            "/api/v1/auth/change-password/",
            {
                "current_password": "WrongOldPassword!",
                "new_password": "NewSecurePass999!",
            },
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 400
        assert resp.data["error"] == "invalid_password"


# ------------------------------------------------------------------
# Guest profiles
# ------------------------------------------------------------------

class TestGuestProfiles:
    def test_guest_profile_create(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post(
            "/api/v1/auth/guest-profiles/",
            {"display_name": "Guest A"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 201
        assert resp.data["display_name"] == "Guest A"
        assert resp.data["is_active"] is False

    def test_guest_profile_max_enforced(self, admin_user):
        """Creating more than 5 guest profiles per session returns 400."""
        client = APIClient()
        _login(client)
        for i in range(5):
            resp = client.post(
                "/api/v1/auth/guest-profiles/",
                {"display_name": f"Guest {i}"},
                format="json",
                HTTP_X_WORKSTATION_ID="ws-001",
            )
            assert resp.status_code == 201

        resp = client.post(
            "/api/v1/auth/guest-profiles/",
            {"display_name": "Guest 6"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 400
        assert resp.data["error"] == "max_profiles_reached"

    def test_guest_profile_activate(self, admin_user):
        client = APIClient()
        _login(client)
        create_resp = client.post(
            "/api/v1/auth/guest-profiles/",
            {"display_name": "Guest Activate"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        profile_id = create_resp.data["id"]

        activate_resp = client.post(
            f"/api/v1/auth/guest-profiles/{profile_id}/activate/",
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert activate_resp.status_code == 200
        assert activate_resp.data["is_active"] is True


# ------------------------------------------------------------------
# Sudo mode
# ------------------------------------------------------------------

class TestSudoMode:
    def test_sudo_acquire_success(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post(
            "/api/v1/sudo/acquire/",
            {"password": "AdminPass123!", "action_class": "user_disable"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 200
        assert resp.data["action_class"] == "user_disable"
        assert "expires_at" in resp.data

    def test_sudo_acquire_wrong_password(self, admin_user):
        client = APIClient()
        _login(client)
        resp = client.post(
            "/api/v1/sudo/acquire/",
            {"password": "WrongPass!", "action_class": "user_disable"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 401
        assert resp.data["error"] == "invalid_password"

    def test_sudo_acquire_non_admin(self, frontdesk_user):
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"username": "frontdesk_user", "password": "FrontDesk123!"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 200

        resp = client.post(
            "/api/v1/sudo/acquire/",
            {"password": "FrontDesk123!", "action_class": "user_disable"},
            format="json",
            HTTP_X_WORKSTATION_ID="ws-001",
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

class TestHealthCheck:
    def test_health_check_public_minimal(self):
        """Unauthenticated health check returns minimal response (no checks detail)."""
        client = APIClient()
        resp = client.get("/api/v1/health/")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "version" in data
        # Public response must NOT include component-level checks
        assert "checks" not in data

    def test_health_check_admin_detailed(self, auth_client):
        """Admin gets detailed component checks."""
        resp = auth_client.get("/api/v1/health/")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data
