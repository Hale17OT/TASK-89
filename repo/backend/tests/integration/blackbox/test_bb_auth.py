"""Black-box tests: Auth, CSRF, Session, Guest Profiles, Change Password."""
import json
import uuid

from .conftest import WS, admin, anon, assert_denied


class TestHealth:
    def test_health_ok(self):
        r = anon().get("/api/v1/health/", **WS)
        assert r.status_code in (200, 503)
        body = r.json()
        assert "status" in body
        assert body["status"] in ("ok", "degraded")
        assert "version" in body

    def test_health_admin_detail(self):
        r = admin().get("/api/v1/health/", **WS)
        assert r.status_code in (200, 503)
        body = r.json()
        assert "status" in body


class TestAuthLogin:
    def test_login_success(self):
        from django.test import Client
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "bb_admin", "password": "Pass1234!"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "user" in body
        assert body["user"]["username"] == "bb_admin"
        assert body["user"]["role"] == "admin"

    def test_login_bad_password(self):
        from django.test import Client
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "bb_admin", "password": "wrong"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 401
        body = r.json()
        assert "error" in body

    def test_login_nonexistent_user(self):
        from django.test import Client
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "nope", "password": "nope"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 401
        body = r.json()
        assert "error" in body


class TestAuthLogout:
    def test_logout_authenticated(self):
        r = admin().post("/api/v1/auth/logout/", **WS)
        assert r.status_code == 204

    def test_logout_anon_denied(self):
        assert_denied(anon().post("/api/v1/auth/logout/", **WS))


class TestAuthSession:
    def test_session_info(self):
        r = admin().get("/api/v1/auth/session/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "user" in body
        assert body["user"]["username"] == "bb_admin"

    def test_session_info_anon_denied(self):
        assert_denied(anon().get("/api/v1/auth/session/", **WS))

    def test_session_refresh(self):
        r = admin().post("/api/v1/auth/session/refresh/", **WS)
        assert r.status_code == 200

    def test_session_refresh_anon_denied(self):
        assert_denied(anon().post("/api/v1/auth/session/refresh/", **WS))


class TestChangePassword:
    def test_change_password_success(self):
        r = admin().post(
            "/api/v1/auth/change-password/",
            json.dumps({
                "current_password": "Pass1234!",
                "new_password": "NewStrongP@ss1234!",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_change_password_wrong_current(self):
        r = admin().post(
            "/api/v1/auth/change-password/",
            json.dumps({
                "current_password": "wrong",
                "new_password": "NewStrongP@ss1234!",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 400
        body = r.json()
        assert "error" in body or "current_password" in body

    def test_change_password_anon_denied(self):
        assert_denied(anon().post(
            "/api/v1/auth/change-password/",
            json.dumps({
                "current_password": "Pass1234!",
                "new_password": "NewStrongP@ss1234!",
            }),
            content_type="application/json",
            **WS,
        ))
