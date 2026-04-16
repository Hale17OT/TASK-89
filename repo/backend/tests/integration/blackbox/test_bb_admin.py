"""Black-box tests: Users, Workstations, Sudo, Audit, Export, Policies."""
import json
import uuid

from apps.accounts.models import User

from .conftest import (
    WS, admin, frontdesk, anon, admin_with_sudo,
    assert_denied, assert_role_denied,
)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class TestUserList:
    def test_user_list(self):
        r = admin().get("/api/v1/users/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "results" in body
        assert body["count"] >= 4

    def test_user_list_frontdesk_denied(self):
        assert_role_denied(frontdesk().get("/api/v1/users/", **WS))


class TestUserCreate:
    def test_user_create(self):
        r = admin().post(
            "/api/v1/users/",
            json.dumps({
                "username": "newuser_bb",
                "password": "NewUser1234!",
                "role": "front_desk",
                "full_name": "New User",
                "email": "new@example.com",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["username"] == "newuser_bb"
        assert body["role"] == "front_desk"


class TestUserDisable:
    def test_user_disable_success_with_sudo(self):
        uid = str(User.objects.get(username="bb_clin").pk)
        c = admin_with_sudo("user_disable")
        r = c.post(
            f"/api/v1/users/{uid}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["is_active"] is False

    def test_user_disable_no_sudo(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = admin().post(
            f"/api/v1/users/{uid}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403
        assert r.json()["error"] == "sudo_required"


class TestUserEnable:
    def test_user_enable_success(self):
        user = User.objects.get(username="bb_clin")
        user.is_active = False
        user.save(update_fields=["is_active"])
        r = admin().post(
            f"/api/v1/users/{user.pk}/enable/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["is_active"] is True


# ---------------------------------------------------------------------------
# Workstations
# ---------------------------------------------------------------------------

class TestWorkstationUnblock:
    def test_workstation_unblock_success(self):
        from apps.accounts.models import WorkstationBlacklist
        bl = WorkstationBlacklist.objects.create(
            client_ip="10.0.0.88", workstation_id="ws-block-bb", is_active=True,
        )
        c = admin_with_sudo("workstation_unblock")
        r = c.post(f"/api/v1/workstations/{bl.pk}/unblock/", **WS)
        assert r.status_code == 200
        bl.refresh_from_db()
        assert bl.is_active is False

    def test_workstation_unblock_no_sudo(self):
        r = admin().post("/api/v1/workstations/99999/unblock/", **WS)
        assert r.status_code == 403
        assert r.json()["error"] == "sudo_required"


# ---------------------------------------------------------------------------
# Sudo
# ---------------------------------------------------------------------------

class TestSudoAcquire:
    def test_sudo_acquire(self):
        r = admin().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "Pass1234!", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["action_class"] == "user_disable"
        assert "expires_at" in body
        assert "expires_in_seconds" in body

    def test_sudo_acquire_bad_password(self):
        r = admin().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "wrong", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)
        assert "error" in r.json() or "detail" in r.json()


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class TestAuditDetail:
    def test_audit_detail_success(self):
        from apps.audit.service import create_audit_entry
        entry = create_audit_entry(
            event_type="test_bb_detail",
            target_model="Test",
            target_id="1",
            target_repr="test",
        )
        r = admin().get(f"/api/v1/audit/entries/{entry.pk}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["event_type"] == "test_bb_detail"

    def test_audit_detail_not_found(self):
        r = admin().get("/api/v1/audit/entries/999999/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"


class TestAuditPurge:
    def test_purge_success_with_sudo(self):
        c = admin_with_sudo("log_purge")
        r = c.post(
            "/api/v1/audit/purge/",
            json.dumps({"confirm": True, "before_date": "2017-01-01T00:00:00Z"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "deleted_count" in body

    def test_purge_no_sudo(self):
        r = admin().post(
            "/api/v1/audit/purge/",
            json.dumps({"confirm": True, "before_date": "2017-01-01T00:00:00Z"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403
        assert r.json()["error"] == "sudo_required"


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

class TestPolicyUpdate:
    def test_policy_update_success_with_sudo(self):
        from apps.accounts.models import SystemPolicy
        SystemPolicy.objects.create(
            key="bb_test_policy", value="old", description="Test",
        )
        c = admin_with_sudo("policy_update")
        r = c.patch(
            "/api/v1/policies/bb_test_policy/",
            json.dumps({"value": "new_val", "confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["value"] == "new_val"
        assert body["key"] == "bb_test_policy"

    def test_policy_update_no_sudo(self):
        r = admin().patch(
            "/api/v1/policies/any_key/",
            json.dumps({"value": "x", "confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403
        assert r.json()["error"] == "sudo_required"

    def test_policy_update_anon_denied(self):
        assert_denied(anon().patch(
            "/api/v1/policies/any_key/",
            json.dumps({"value": "x", "confirm": True}),
            content_type="application/json",
            **WS,
        ))
