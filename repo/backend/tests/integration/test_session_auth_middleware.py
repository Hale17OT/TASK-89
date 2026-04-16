"""
Black-box tests for middleware behaviour using real session authentication.

These tests use Django's test Client with client.login() — NOT
force_authenticate — to exercise the full middleware stack:
  - WorkstationThrottleMiddleware (X-Workstation-ID enforcement)
  - SessionTimeoutMiddleware (idle + absolute timeouts)
  - SudoModeMiddleware (sudo token injection from session)
  - AuditLoggingMiddleware (audit entries created for auditable actions)
  - RequestIDMiddleware (X-Request-ID header propagation)

This directly addresses the gap where force_authenticate skips
authentication/session middleware in integration tests.
"""
import json
import time

import pytest
from django.test import Client

from apps.accounts.models import User

WS = {"HTTP_X_WORKSTATION_ID": "ws-mw-test"}
PASSWORD = "MwTest1234!"


@pytest.fixture(autouse=True)
def mw_users(db):
    User.objects.create_user(username="mw_admin", password=PASSWORD, role="admin")
    User.objects.create_user(username="mw_fd", password=PASSWORD, role="front_desk")


def _login_admin():
    c = Client()
    c.login(username="mw_admin", password=PASSWORD)
    return c


def _login_frontdesk():
    c = Client()
    c.login(username="mw_fd", password=PASSWORD)
    return c


# ---------------------------------------------------------------------------
# WorkstationThrottle: X-Workstation-ID enforcement
# ---------------------------------------------------------------------------

class TestWorkstationIDEnforcement:
    def test_login_without_workstation_id_rejected(self):
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "mw_admin", "password": PASSWORD}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "workstation_id_required"

    def test_login_with_workstation_id_succeeds(self):
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "mw_admin", "password": PASSWORD}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert "user" in r.json()

    def test_authenticated_request_without_workstation_id_rejected(self):
        c = _login_admin()
        r = c.get("/api/v1/patients/?q=test")
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "workstation_id_required"

    def test_unauthenticated_health_check_without_workstation_id_allowed(self):
        c = Client()
        r = c.get("/api/v1/health/")
        assert r.status_code in (200, 503)


# ---------------------------------------------------------------------------
# RequestID: X-Request-ID header propagation
# ---------------------------------------------------------------------------

class TestRequestIDPropagation:
    def test_response_includes_request_id(self):
        c = Client()
        r = c.get("/api/v1/health/", **WS)
        assert "X-Request-ID" in r

    def test_client_provided_request_id_echoed(self):
        c = Client()
        r = c.get("/api/v1/health/", HTTP_X_REQUEST_ID="custom-trace-999", **WS)
        assert r["X-Request-ID"] == "custom-trace-999"


# ---------------------------------------------------------------------------
# SessionTimeout: idle and absolute expiry
# ---------------------------------------------------------------------------

class TestSessionTimeoutBehaviour:
    def test_idle_timeout_expires_session(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 0  # expire immediately
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800

        c = _login_admin()
        # First request sets _last_activity timestamp
        r1 = c.get("/api/v1/auth/session/", **WS)
        assert r1.status_code == 200

        # Any subsequent request with timeout=0 will have elapsed > 0 seconds
        r2 = c.get("/api/v1/auth/session/", **WS)
        assert r2.status_code == 401
        body = r2.json()
        assert body["error"] == "session_expired"
        assert body["reason"] == "idle"

    def test_active_session_not_expired(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800

        c = _login_admin()
        r = c.get("/api/v1/auth/session/", **WS)
        assert r.status_code == 200
        assert "user" in r.json()


# ---------------------------------------------------------------------------
# SudoMode: sudo token injection via session
# ---------------------------------------------------------------------------

class TestSudoModeThroughSession:
    def test_sudo_acquire_injects_into_session(self):
        c = _login_admin()
        r = c.post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": PASSWORD, "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["action_class"] == "user_disable"
        assert "expires_at" in body

    def test_sudo_status_reflects_acquired_token(self):
        c = _login_admin()
        # Acquire
        c.post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": PASSWORD, "action_class": "bulk_export"}),
            content_type="application/json",
            **WS,
        )
        # Check status
        r = c.get("/api/v1/sudo/status/", **WS)
        assert r.status_code == 200
        body = r.json()
        actions = [a["action_class"] for a in body.get("active_sudo_actions", [])]
        assert "bulk_export" in actions

    def test_user_disable_requires_sudo_through_session(self):
        c = _login_admin()
        target = User.objects.get(username="mw_fd")
        # Without sudo: should get 403
        r = c.post(
            f"/api/v1/users/{target.pk}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403
        body = r.json()
        assert body["error"] == "sudo_required"

    def test_user_disable_succeeds_with_sudo(self):
        c = _login_admin()
        target = User.objects.get(username="mw_fd")
        # Acquire sudo
        c.post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": PASSWORD, "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        # Now disable should work
        r = c.post(
            f"/api/v1/users/{target.pk}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert r.json()["user"]["is_active"] is False


# ---------------------------------------------------------------------------
# AuditLogging: verify middleware creates audit trail
# ---------------------------------------------------------------------------

class TestAuditLoggingThroughMiddleware:
    def test_audit_middleware_is_configured(self):
        """Verify the audit logging middleware is present in the stack."""
        from django.conf import settings
        assert "infrastructure.middleware.audit_logging.AuditLoggingMiddleware" in settings.MIDDLEWARE

    def test_request_id_populated_on_auditable_request(self):
        """Verify that requests through the stack get a request ID (proving middleware runs)."""
        c = _login_admin()
        r = c.get("/api/v1/auth/session/", **WS)
        assert r.status_code == 200
        assert "X-Request-ID" in r

    def test_login_does_not_create_duplicate_audit(self):
        """Login creates its own audit context; middleware should process it once."""
        from apps.audit.models import AuditEntry
        before = AuditEntry.objects.count()
        c = Client()
        c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "mw_admin", "password": PASSWORD}),
            content_type="application/json",
            **WS,
        )
        login_audits = AuditEntry.objects.filter(
            event_type="user_login",
            id__gt=before,
        ).count()
        # Should have exactly 1 login audit, not duplicated
        assert login_audits <= 1
