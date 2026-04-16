"""Unit tests for custom middleware: RequestID, SudoMode, SessionTimeout,
EncryptionContext, AuditLogging, WorkstationThrottle.

Each middleware is tested by instantiating it directly with a fake
get_response callable and feeding it a minimal request object,
verifying side-effects (request attrs, response headers, early returns).
"""
import json as _json
import time
import uuid

import pytest
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from types import SimpleNamespace


def _parse_json_response(resp):
    """Parse JSON body from either JsonResponse or HttpResponse."""
    if hasattr(resp, "json") and callable(resp.json):
        return resp.json()
    return _json.loads(resp.content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_response(request):
    return HttpResponse("ok", status=200)


def _make_request(path="/api/v1/test/", method="GET", user=None, headers=None, cookies=None):
    """Build a minimal Django HttpRequest for middleware testing."""
    req = HttpRequest()
    req.method = method
    req.path = path
    req.META["REMOTE_ADDR"] = "127.0.0.1"
    req.META["SERVER_NAME"] = "localhost"
    req.META["SERVER_PORT"] = "8000"
    if headers:
        for k, v in headers.items():
            meta_key = f"HTTP_{k.upper().replace('-', '_')}"
            req.META[meta_key] = v
    if cookies:
        req.COOKIES.update(cookies)
    if user is None:
        req.user = SimpleNamespace(is_authenticated=False, pk=None, username="anonymous")
    else:
        req.user = user
    # Attach a session
    req.session = SessionStore()
    return req


def _authed_user(role="admin", pk=1, username="testuser"):
    return SimpleNamespace(
        is_authenticated=True,
        pk=pk,
        username=username,
        role=role,
    )


# ---------------------------------------------------------------------------
# RequestIDMiddleware
# ---------------------------------------------------------------------------

class TestRequestIDMiddleware:
    def _get_mw(self):
        from infrastructure.middleware.request_id import RequestIDMiddleware
        return RequestIDMiddleware(_ok_response)

    def test_generates_request_id_when_not_provided(self):
        mw = self._get_mw()
        req = _make_request()
        resp = mw(req)
        assert hasattr(req, "request_id")
        assert len(req.request_id) == 36  # UUID format
        assert resp["X-Request-ID"] == req.request_id

    def test_preserves_client_provided_request_id(self):
        mw = self._get_mw()
        custom_id = "custom-trace-12345"
        req = _make_request(headers={"X-Request-ID": custom_id})
        resp = mw(req)
        assert req.request_id == custom_id
        assert resp["X-Request-ID"] == custom_id

    def test_response_always_has_header(self):
        mw = self._get_mw()
        req = _make_request()
        resp = mw(req)
        assert "X-Request-ID" in resp


# ---------------------------------------------------------------------------
# SudoModeMiddleware
# ---------------------------------------------------------------------------

class TestSudoModeMiddleware:
    def _get_mw(self):
        from infrastructure.middleware.sudo_mode import SudoModeMiddleware
        return SudoModeMiddleware(_ok_response)

    def test_unauthenticated_gets_empty_sudo_actions(self):
        mw = self._get_mw()
        req = _make_request()
        mw(req)
        assert req.sudo_actions == set()

    def test_authenticated_no_tokens_gets_empty(self):
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        mw(req)
        assert req.sudo_actions == set()

    def test_authenticated_with_active_token(self):
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_sudo_tokens"] = {
            "user_disable": {"expires_at": time.time() + 300},
        }
        mw(req)
        assert "user_disable" in req.sudo_actions

    def test_expired_token_excluded(self):
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_sudo_tokens"] = {
            "user_disable": {"expires_at": time.time() - 10},
        }
        mw(req)
        assert "user_disable" not in req.sudo_actions

    def test_mixed_active_and_expired(self):
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_sudo_tokens"] = {
            "user_disable": {"expires_at": time.time() + 300},
            "bulk_export": {"expires_at": time.time() - 10},
        }
        mw(req)
        assert "user_disable" in req.sudo_actions
        assert "bulk_export" not in req.sudo_actions

    def test_expired_tokens_cleaned_from_session(self):
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_sudo_tokens"] = {
            "user_disable": {"expires_at": time.time() + 300},
            "bulk_export": {"expires_at": time.time() - 10},
        }
        mw(req)
        assert "bulk_export" not in req.session["_sudo_tokens"]
        assert "user_disable" in req.session["_sudo_tokens"]


# ---------------------------------------------------------------------------
# SessionTimeoutMiddleware
# ---------------------------------------------------------------------------

class TestSessionTimeoutMiddleware:
    def _get_mw(self):
        from infrastructure.middleware.session_timeout import SessionTimeoutMiddleware
        return SessionTimeoutMiddleware(_ok_response)

    def test_unauthenticated_passes_through(self):
        mw = self._get_mw()
        req = _make_request()
        resp = mw(req)
        assert resp.status_code == 200

    def test_first_request_sets_timestamps(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        resp = mw(req)
        assert resp.status_code == 200
        assert "_last_activity" in req.session
        assert "_session_created" in req.session

    def test_idle_timeout_triggers_401(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_last_activity"] = time.time() - 1000  # 1000s ago > 900
        req.session["_session_created"] = time.time() - 1000
        resp = mw(req)
        assert resp.status_code == 401
        body = _parse_json_response(resp)
        assert body.get("error") == "session_expired"
        assert body.get("reason") == "idle"

    def test_absolute_timeout_triggers_401(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_last_activity"] = time.time() - 10  # recent
        req.session["_session_created"] = time.time() - 30000  # 30000s > 28800
        resp = mw(req)
        assert resp.status_code == 401
        body = _parse_json_response(resp)
        assert body.get("error") == "session_expired"
        assert body.get("reason") == "absolute"

    def test_active_session_passes_through(self, settings):
        settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900
        settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800
        mw = self._get_mw()
        req = _make_request(user=_authed_user())
        req.session["_last_activity"] = time.time() - 10
        req.session["_session_created"] = time.time() - 100
        resp = mw(req)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# EncryptionContextMiddleware
# ---------------------------------------------------------------------------

class TestEncryptionContextMiddleware:
    def _get_mw(self):
        from infrastructure.middleware.encryption_context import EncryptionContextMiddleware
        return EncryptionContextMiddleware(_ok_response)

    def test_exempt_path_passes_when_not_initialized(self):
        from infrastructure.encryption.service import encryption_service
        old_key = encryption_service._master_key
        encryption_service._master_key = None
        try:
            mw = self._get_mw()
            req = _make_request(path="/api/v1/health/")
            resp = mw(req)
            assert resp.status_code == 200
        finally:
            encryption_service._master_key = old_key

    def test_non_exempt_path_returns_503_when_not_initialized(self):
        from infrastructure.encryption.service import encryption_service
        old_key = encryption_service._master_key
        encryption_service._master_key = None
        try:
            mw = self._get_mw()
            req = _make_request(path="/api/v1/patients/")
            resp = mw(req)
            assert resp.status_code == 503
            body = _parse_json_response(resp)
            assert body.get("error") == "encryption_not_ready"
        finally:
            encryption_service._master_key = old_key

    def test_passes_when_initialized(self):
        mw = self._get_mw()
        req = _make_request(path="/api/v1/patients/")
        resp = mw(req)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# AuditLoggingMiddleware
# ---------------------------------------------------------------------------

class TestAuditLoggingMiddleware:
    def _get_mw(self):
        from infrastructure.middleware.audit_logging import AuditLoggingMiddleware
        return AuditLoggingMiddleware(_ok_response)

    def test_no_audit_context_does_not_create_entry(self, db):
        from apps.audit.models import AuditEntry
        before = AuditEntry.objects.count()
        mw = self._get_mw()
        req = _make_request()
        mw(req)
        assert AuditEntry.objects.count() == before

    def test_audit_context_creates_entry(self, db, admin_user):
        from apps.audit.models import AuditEntry
        before = AuditEntry.objects.count()

        def view_that_sets_audit(request):
            request._audit_context = {
                "event_type": "test_event",
                "target_model": "TestModel",
                "target_id": "123",
                "target_repr": "Test entry",
            }
            return HttpResponse("ok", status=200)

        from infrastructure.middleware.audit_logging import AuditLoggingMiddleware
        mw = AuditLoggingMiddleware(view_that_sets_audit)
        req = _make_request(user=admin_user)
        req.client_ip = "10.0.0.1"
        req.workstation_id = "ws-test"
        mw(req)

        assert AuditEntry.objects.count() == before + 1
        entry = AuditEntry.objects.order_by("-id").first()
        assert entry.event_type == "test_event"
        assert entry.target_model == "TestModel"
