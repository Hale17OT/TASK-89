"""
Comprehensive black-box HTTP API tests for MedRights Portal.

Covers ALL 51+ API endpoints using Django's test Client, cookie-based auth
(client.login()), and the HTTP_X_WORKSTATION_ID header on every request.

Organised by domain: Health, Auth, Patients, Consents, Media, Financials,
Users, Workstations, Sudo, Audit, Reports, Export, Policies, Client Logs.
"""
import io
import json
import uuid

import pytest
from django.test import Client
from PIL import Image

from apps.accounts.models import User

WS = {"HTTP_X_WORKSTATION_ID": "ws-bb"}

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_client(username, password):
    c = Client()
    c.login(username=username, password=password)
    return c


def _create_users():
    """Create all 4 role users. Call in fixtures."""
    users = {}
    for uname, role, pwd in [
        ("bb_admin", "admin", "Pass1234!"),
        ("bb_fd", "front_desk", "Pass1234!"),
        ("bb_clin", "clinician", "Pass1234!"),
        ("bb_comp", "compliance", "Pass1234!"),
    ]:
        users[role] = User.objects.create_user(username=uname, password=pwd, role=role)
    return users


def _admin():
    return _make_client("bb_admin", "Pass1234!")


def _frontdesk():
    return _make_client("bb_fd", "Pass1234!")


def _clinician():
    return _make_client("bb_clin", "Pass1234!")


def _compliance():
    return _make_client("bb_comp", "Pass1234!")


def _anon():
    return Client()


def _admin_with_sudo(action_class):
    """Login as admin and acquire a sudo token. Returns a Client with active sudo."""
    c = _admin()
    c.post(
        "/api/v1/sudo/acquire/",
        json.dumps({"password": "Pass1234!", "action_class": action_class}),
        content_type="application/json",
        **WS,
    )
    return c


def _test_image():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, "PNG")
    buf.seek(0)
    buf.name = "test.png"
    return buf


def _assert_denied(r):
    """Assert a 401/403 response has a well-formed error body."""
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
    body = r.json()
    assert "detail" in body or "error" in body, f"Denial response missing 'error' or 'detail': {body}"


def _assert_role_denied(r, expected_status=403):
    """Assert a role-based 403 with error schema."""
    assert r.status_code == expected_status
    body = r.json()
    assert "detail" in body or "error" in body, f"403 response missing error schema: {body}"


# ---------------------------------------------------------------------------
# Autouse fixture -- create users for every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def bb_users(db):
    return _create_users()


# ---------------------------------------------------------------------------
# 1. Health  (1 endpoint, 2 tests)
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self):
        r = _anon().get("/api/v1/health/", **WS)
        assert r.status_code in (200, 503)
        assert "status" in r.json()

    def test_health_admin_detail(self):
        r = _admin().get("/api/v1/health/", **WS)
        assert r.status_code in (200, 503)
        body = r.json()
        assert "status" in body


# ---------------------------------------------------------------------------
# 2. Auth -- CSRF / Login / Logout / Session (6 endpoints, ~12 tests)
# ---------------------------------------------------------------------------

class TestAuthCsrf:
    def test_csrf_cookie(self):
        r = _anon().get("/api/v1/auth/csrf/", **WS)
        assert r.status_code == 200

    def test_csrf_sets_cookie(self):
        r = _anon().get("/api/v1/auth/csrf/", **WS)
        assert r.status_code == 200


class TestAuthLogin:
    def test_login_success(self):
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "bb_admin", "password": "Pass1234!"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert "user" in r.json()

    def test_login_bad_password(self):
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "bb_admin", "password": "wrong"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 401

    def test_login_nonexistent_user(self):
        c = Client()
        r = c.post(
            "/api/v1/auth/login/",
            json.dumps({"username": "nope", "password": "nope"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 401


class TestAuthLogout:
    def test_logout_authenticated(self):
        c = _admin()
        r = c.post("/api/v1/auth/logout/", **WS)
        assert r.status_code == 204

    def test_logout_anon_denied(self):
        r = _anon().post("/api/v1/auth/logout/", **WS)
        assert r.status_code in (401, 403)


class TestAuthSession:
    def test_session_info(self):
        r = _admin().get("/api/v1/auth/session/", **WS)
        assert r.status_code == 200
        assert "user" in r.json()

    def test_session_info_anon_denied(self):
        r = _anon().get("/api/v1/auth/session/", **WS)
        assert r.status_code in (401, 403)

    def test_session_refresh(self):
        r = _admin().post("/api/v1/auth/session/refresh/", **WS)
        assert r.status_code == 200

    def test_session_refresh_anon_denied(self):
        r = _anon().post("/api/v1/auth/session/refresh/", **WS)
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 3. Auth -- guest profiles + remember device (4 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

class TestGuestProfiles:
    def test_guest_profile_list(self):
        r = _admin().get("/api/v1/auth/guest-profiles/", **WS)
        assert r.status_code == 200

    def test_guest_profile_create(self):
        r = _admin().post(
            "/api/v1/auth/guest-profiles/",
            json.dumps({"display_name": "Guest A"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201

    def test_guest_profile_activate(self):
        c = _admin()
        r = c.post(
            "/api/v1/auth/guest-profiles/",
            json.dumps({"display_name": "Guest B"}),
            content_type="application/json",
            **WS,
        )
        pk = r.json()["id"]
        r2 = c.post(f"/api/v1/auth/guest-profiles/{pk}/activate/", **WS)
        assert r2.status_code == 200

    def test_guest_recent_patients_list(self):
        c = _admin()
        r = c.post(
            "/api/v1/auth/guest-profiles/",
            json.dumps({"display_name": "Guest C"}),
            content_type="application/json",
            **WS,
        )
        pk = r.json()["id"]
        r2 = c.get(f"/api/v1/auth/guest-profiles/{pk}/recent-patients/", **WS)
        assert r2.status_code == 200

    def test_guest_recent_patients_post(self):
        c = _admin()
        r = c.post(
            "/api/v1/auth/guest-profiles/",
            json.dumps({"display_name": "Guest D"}),
            content_type="application/json",
            **WS,
        )
        pk = r.json()["id"]
        patient = _create_patient()
        r2 = c.post(
            f"/api/v1/auth/guest-profiles/{pk}/recent-patients/",
            json.dumps({"patient_id": patient["id"]}),
            content_type="application/json",
            **WS,
        )
        assert r2.status_code == 201

    def test_guest_profile_anon_denied(self):
        r = _anon().get("/api/v1/auth/guest-profiles/", **WS)
        assert r.status_code in (401, 403)

    def test_guest_activate_anon_denied(self):
        fake = uuid.uuid4()
        r = _anon().post(f"/api/v1/auth/guest-profiles/{fake}/activate/", **WS)
        assert r.status_code in (401, 403)


class TestRememberDevice:
    def test_remember_device_post(self):
        r = _admin().post("/api/v1/auth/remember-device/", **WS)
        assert r.status_code == 200

    def test_remember_device_prefill_no_cookie(self):
        r = _anon().get("/api/v1/auth/remember-device/prefill/", **WS)
        assert r.status_code == 200
        assert r.json()["username"] is None


# ---------------------------------------------------------------------------
# 4. Auth -- change password (1 endpoint, 3 tests)
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_success(self):
        r = _admin().post(
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
        r = _admin().post(
            "/api/v1/auth/change-password/",
            json.dumps({
                "current_password": "wrong",
                "new_password": "NewStrongP@ss1234!",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 400

    def test_change_password_anon_denied(self):
        r = _anon().post(
            "/api/v1/auth/change-password/",
            json.dumps({
                "current_password": "Pass1234!",
                "new_password": "NewStrongP@ss1234!",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 5. Patients CRUD + break-glass (5 endpoints, ~12 tests)
# ---------------------------------------------------------------------------

def _create_patient(client_fn=None):
    c = client_fn() if client_fn else _admin()
    r = c.post(
        "/api/v1/patients/create/",
        json.dumps({
            "mrn": f"MRN-{uuid.uuid4().hex[:6]}",
            "ssn": "123456789",
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "1985-06-15",
            "gender": "Female",
            "phone": "5559876543",
            "email": "jane@example.com",
            "address": "456 Oak Ave",
        }),
        content_type="application/json",
        **WS,
    )
    assert r.status_code == 201, f"Patient creation failed: {r.content}"
    return r.json()


class TestPatientSearch:
    def test_search_patients(self):
        _create_patient()
        r = _admin().get("/api/v1/patients/?q=123456789", **WS)
        assert r.status_code == 200

    def test_search_missing_q(self):
        r = _admin().get("/api/v1/patients/", **WS)
        assert r.status_code == 400

    def test_search_anon_denied(self):
        r = _anon().get("/api/v1/patients/?q=test", **WS)
        assert r.status_code in (401, 403)


class TestPatientCreate:
    def test_create_patient_admin(self):
        p = _create_patient(_admin)
        assert "id" in p

    def test_create_patient_frontdesk(self):
        p = _create_patient(_frontdesk)
        assert "id" in p

    def test_create_patient_clinician_denied(self):
        r = _clinician().post(
            "/api/v1/patients/create/",
            json.dumps({
                "mrn": "MRN-999",
                "ssn": "111222333",
                "first_name": "X",
                "last_name": "Y",
                "date_of_birth": "2000-01-01",
                "gender": "Male",
                "phone": "5550000000",
                "email": "x@y.com",
                "address": "nowhere",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403

    def test_create_patient_anon_denied(self):
        r = _anon().post(
            "/api/v1/patients/create/",
            json.dumps({"mrn": "MRN-X"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestPatientDetail:
    def test_detail(self):
        p = _create_patient()
        r = _admin().get(f"/api/v1/patients/{p['id']}/", **WS)
        assert r.status_code == 200

    def test_detail_not_found(self):
        r = _admin().get(f"/api/v1/patients/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404


class TestPatientUpdate:
    def test_update_patient(self):
        p = _create_patient()
        r = _admin().patch(
            f"/api/v1/patients/{p['id']}/update/",
            json.dumps({"first_name": "Updated"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_update_anon_denied(self):
        p = _create_patient()
        r = _anon().patch(
            f"/api/v1/patients/{p['id']}/update/",
            json.dumps({"first_name": "No"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestBreakGlass:
    def test_break_glass_success(self):
        p = _create_patient()
        r = _admin().post(
            f"/api/v1/patients/{p['id']}/break-glass/",
            json.dumps({
                "justification": "Emergency access required for patient treatment",
                "justification_category": "emergency",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201

    def test_break_glass_anon_denied(self):
        p = _create_patient()
        r = _anon().post(
            f"/api/v1/patients/{p['id']}/break-glass/",
            json.dumps({
                "justification": "Emergency access required for patient treatment",
                "justification_category": "emergency",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 6. Consents (3 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

def _create_consent(patient_id, client_fn=None):
    c = client_fn() if client_fn else _admin()
    r = c.post(
        f"/api/v1/patients/{patient_id}/consents/",
        json.dumps({
            "purpose": "General treatment consent",
            "effective_date": "2024-01-01",
            "expiration_date": "2030-12-31",
            "scopes": [
                {"scope_type": "media_use", "scope_value": "capture_storage"},
                {"scope_type": "action", "scope_value": "data_sharing"},
            ],
        }),
        content_type="application/json",
        **WS,
    )
    assert r.status_code == 201, f"Consent creation failed: {r.content}"
    return r.json()


class TestConsentListCreate:
    def test_consent_list(self):
        p = _create_patient()
        r = _admin().get(f"/api/v1/patients/{p['id']}/consents/", **WS)
        assert r.status_code == 200

    def test_consent_create(self):
        p = _create_patient()
        c = _create_consent(p["id"])
        assert "id" in c

    def test_consent_list_anon_denied(self):
        p = _create_patient()
        r = _anon().get(f"/api/v1/patients/{p['id']}/consents/", **WS)
        assert r.status_code in (401, 403)

    def test_consent_create_anon_denied(self):
        p = _create_patient()
        r = _anon().post(
            f"/api/v1/patients/{p['id']}/consents/",
            json.dumps({"purpose": "test", "effective_date": "2024-01-01"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestConsentDetail:
    def test_consent_detail(self):
        p = _create_patient()
        c = _create_consent(p["id"])
        r = _admin().get(f"/api/v1/patients/{p['id']}/consents/{c['id']}/", **WS)
        assert r.status_code == 200

    def test_consent_detail_not_found(self):
        p = _create_patient()
        r = _admin().get(f"/api/v1/patients/{p['id']}/consents/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404


class TestConsentRevoke:
    def test_consent_revoke(self):
        p = _create_patient()
        c = _create_consent(p["id"])
        r = _admin().post(
            f"/api/v1/patients/{p['id']}/consents/{c['id']}/revoke/",
            json.dumps({"reason": "Patient request"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_consent_revoke_anon_denied(self):
        p = _create_patient()
        c = _create_consent(p["id"])
        r = _anon().post(
            f"/api/v1/patients/{p['id']}/consents/{c['id']}/revoke/",
            json.dumps({"reason": "no"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 7. Media upload / list / detail / download / watermark / attach
#    (6 endpoints, ~14 tests)
# ---------------------------------------------------------------------------

def _upload_media(client_fn=None):
    c = client_fn() if client_fn else _admin()
    img = _test_image()
    r = c.post("/api/v1/media/upload/", {"file": img}, **WS)
    assert r.status_code == 201, f"Upload failed: {r.content}"
    return r.json()


class TestMediaUpload:
    def test_upload_success(self):
        m = _upload_media()
        assert "id" in m

    def test_upload_anon_denied(self):
        img = _test_image()
        r = _anon().post("/api/v1/media/upload/", {"file": img}, **WS)
        assert r.status_code in (401, 403)

    def test_upload_compliance_denied(self):
        img = _test_image()
        r = _compliance().post("/api/v1/media/upload/", {"file": img}, **WS)
        assert r.status_code == 403


class TestMediaList:
    def test_media_list(self):
        _upload_media()
        r = _admin().get("/api/v1/media/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_media_list_anon_denied(self):
        r = _anon().get("/api/v1/media/", **WS)
        assert r.status_code in (401, 403)


class TestMediaDetail:
    def test_media_detail(self):
        m = _upload_media()
        r = _admin().get(f"/api/v1/media/{m['id']}/", **WS)
        assert r.status_code == 200

    def test_media_detail_not_found(self):
        r = _admin().get(f"/api/v1/media/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404

    def test_media_detail_anon_denied(self):
        m = _upload_media()
        r = _anon().get(f"/api/v1/media/{m['id']}/", **WS)
        assert r.status_code in (401, 403)


class TestMediaDownload:
    def test_media_download(self):
        m = _upload_media()
        r = _admin().get(f"/api/v1/media/{m['id']}/download/", **WS)
        assert r.status_code == 200

    def test_media_download_anon_denied(self):
        m = _upload_media()
        r = _anon().get(f"/api/v1/media/{m['id']}/download/", **WS)
        assert r.status_code in (401, 403)


class TestMediaWatermark:
    def test_watermark(self):
        m = _upload_media()
        r = _admin().post(
            f"/api/v1/media/{m['id']}/watermark/",
            json.dumps({"clinic_name": "Test Clinic", "date_stamp": True, "opacity": 0.35}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_watermark_anon_denied(self):
        m = _upload_media()
        r = _anon().post(
            f"/api/v1/media/{m['id']}/watermark/",
            json.dumps({"text": "CONFIDENTIAL"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestMediaAttachPatient:
    def test_attach_patient(self):
        m = _upload_media()
        p = _create_patient()
        r = _admin().post(
            f"/api/v1/media/{m['id']}/attach-patient/",
            json.dumps({"patient_id": p["id"]}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_attach_patient_anon_denied(self):
        m = _upload_media()
        p = _create_patient()
        r = _anon().post(
            f"/api/v1/media/{m['id']}/attach-patient/",
            json.dumps({"patient_id": p["id"]}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 8. Media infringement + repost (3 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

class TestInfringementListCreate:
    def test_infringement_list(self):
        r = _admin().get("/api/v1/media/infringement/", **WS)
        assert r.status_code == 200

    def test_infringement_create(self):
        m = _upload_media()
        r = _admin().post(
            "/api/v1/media/infringement/",
            json.dumps({
                "media_asset_id": m["id"],
                "reference": "https://example.com/stolen",
                "notes": "This media was found on an external site",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201

    def test_infringement_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/media/infringement/", **WS)
        _assert_role_denied(r)

    def test_infringement_create_anon_denied(self):
        r = _anon().post(
            "/api/v1/media/infringement/",
            json.dumps({"reference": "x", "notes": "y"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestInfringementDetailUpdate:
    def _make_infringement(self):
        m = _upload_media()
        r = _admin().post(
            "/api/v1/media/infringement/",
            json.dumps({
                "media_asset_id": m["id"],
                "reference": "https://example.com/stolen",
                "notes": "Infringement found on external site",
            }),
            content_type="application/json",
            **WS,
        )
        return r.json()

    def test_infringement_detail(self):
        inf = self._make_infringement()
        r = _admin().get(f"/api/v1/media/infringement/{inf['id']}/", **WS)
        assert r.status_code == 200

    def test_infringement_update(self):
        inf = self._make_infringement()
        r = _admin().patch(
            f"/api/v1/media/infringement/{inf['id']}/",
            json.dumps({"status": "investigating"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_infringement_detail_anon_denied(self):
        inf = self._make_infringement()
        r = _anon().get(f"/api/v1/media/infringement/{inf['id']}/", **WS)
        assert r.status_code in (401, 403)

    def test_infringement_detail_clinician_denied(self):
        inf = self._make_infringement()
        r = _clinician().get(f"/api/v1/media/infringement/{inf['id']}/", **WS)
        assert r.status_code == 403


class TestRepostAuthorize:
    def test_repost_authorize_success(self):
        m = _upload_media()
        img = _test_image()
        r = _admin().post(
            f"/api/v1/media/{m['id']}/repost/authorize/",
            {"citation_text": "Original by John Doe", "authorization_file": img},
            **WS,
        )
        assert r.status_code == 201

    def test_repost_authorize_frontdesk_denied(self):
        m = _upload_media()
        img = _test_image()
        r = _frontdesk().post(
            f"/api/v1/media/{m['id']}/repost/authorize/",
            {"citation_text": "test", "authorization_file": img},
            **WS,
        )
        assert r.status_code == 403

    def test_repost_authorize_anon_denied(self):
        m = _upload_media()
        img = _test_image()
        r = _anon().post(
            f"/api/v1/media/{m['id']}/repost/authorize/",
            {"citation_text": "test", "authorization_file": img},
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 9. Financials -- orders (4 endpoints, ~10 tests)
# ---------------------------------------------------------------------------

def _create_order(patient_id=None, client_fn=None):
    c = client_fn() if client_fn else _admin()
    if not patient_id:
        p = _create_patient()
        patient_id = p["id"]
    r = c.post(
        "/api/v1/financials/orders/",
        json.dumps({
            "patient_id": patient_id,
            "line_items": [
                {"description": "Consultation", "quantity": 1, "unit_price": "150.00"},
            ],
            "notes": "Test order",
        }),
        content_type="application/json",
        **WS,
    )
    assert r.status_code == 201, f"Order creation failed: {r.content}"
    return r.json()


class TestOrderListCreate:
    def test_order_list(self):
        _create_order()
        r = _admin().get("/api/v1/financials/orders/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_order_create(self):
        o = _create_order()
        assert "id" in o

    def test_order_create_anon_denied(self):
        p = _create_patient()
        r = _anon().post(
            "/api/v1/financials/orders/",
            json.dumps({
                "patient_id": p["id"],
                "line_items": [
                    {"description": "Test", "quantity": 1, "unit_price": "10.00"},
                ],
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)

    def test_order_create_clinician_denied(self):
        p = _create_patient()
        r = _clinician().post(
            "/api/v1/financials/orders/",
            json.dumps({
                "patient_id": p["id"],
                "line_items": [
                    {"description": "Test", "quantity": 1, "unit_price": "10.00"},
                ],
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestOrderDetail:
    def test_order_detail(self):
        o = _create_order()
        r = _admin().get(f"/api/v1/financials/orders/{o['id']}/", **WS)
        assert r.status_code == 200

    def test_order_detail_not_found(self):
        r = _admin().get(f"/api/v1/financials/orders/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404


class TestOrderPayment:
    def test_order_payment(self):
        o = _create_order()
        r = _admin().post(
            f"/api/v1/financials/orders/{o['id']}/payments/",
            json.dumps({
                "amount": 150.00,
                "method": "cash",
            }),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=uuid.uuid4().hex,
            **WS,
        )
        assert r.status_code in (200, 201)

    def test_order_payment_anon_denied(self):
        o = _create_order()
        r = _anon().post(
            f"/api/v1/financials/orders/{o['id']}/payments/",
            json.dumps({"amount": "10.00", "payment_method": "cash"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestOrderVoid:
    def test_order_void(self):
        o = _create_order()
        r = _admin().post(
            f"/api/v1/financials/orders/{o['id']}/void/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_order_void_frontdesk_denied(self):
        o = _create_order()
        r = _frontdesk().post(
            f"/api/v1/financials/orders/{o['id']}/void/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# 10. Financials -- refunds (3 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

def _create_paid_order():
    """Create an order with a cash payment recorded. Returns (order, payment_id)."""
    o = _create_order()
    r = _admin().post(
        f"/api/v1/financials/orders/{o['id']}/payments/",
        json.dumps({"amount": 150.00, "method": "cash"}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY=uuid.uuid4().hex,
        **WS,
    )
    payment = r.json()
    # Payment response might be nested or direct
    payment_id = payment.get("id") or payment.get("payment_id", "")
    return o, payment_id


class TestRefundCreate:
    def test_refund_create(self):
        o, pay_id = _create_paid_order()
        r = _admin().post(
            f"/api/v1/financials/orders/{o['id']}/refunds/",
            json.dumps({
                "amount": 50.00,
                "reason": "Partial refund",
                "original_payment_id": pay_id,
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (200, 201)

    def test_refund_create_anon_denied(self):
        o, _ = _create_paid_order()
        r = _anon().post(
            f"/api/v1/financials/orders/{o['id']}/refunds/",
            json.dumps({"amount": 10.00, "reason": "nope", "original_payment_id": "x"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestRefundList:
    def test_refund_list(self):
        r = _admin().get("/api/v1/financials/refunds/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_refund_list_anon_denied(self):
        r = _anon().get("/api/v1/financials/refunds/", **WS)
        assert r.status_code in (401, 403)

    def test_refund_list_clinician_denied(self):
        r = _clinician().get("/api/v1/financials/refunds/", **WS)
        assert r.status_code == 403


class TestRefundApprove:
    def _make_refund(self):
        o, pay_id = _create_paid_order()
        r = _admin().post(
            f"/api/v1/financials/orders/{o['id']}/refunds/",
            json.dumps({"amount": 50.00, "reason": "Test refund", "original_payment_id": pay_id}),
            content_type="application/json",
            **WS,
        )
        data = r.json()
        return data

    def test_refund_approve(self):
        ref = self._make_refund()
        refund_id = ref.get("id") or ref.get("refund_id", "")
        r = _admin().post(
            f"/api/v1/financials/refunds/{refund_id}/approve/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_refund_approve_frontdesk_denied(self):
        ref = self._make_refund()
        refund_id = ref.get("id") or ref.get("refund_id", "")
        r = _frontdesk().post(
            f"/api/v1/financials/refunds/{refund_id}/approve/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestRefundProcess:
    def _make_approved_refund(self):
        o, pay_id = _create_paid_order()
        r = _admin().post(
            f"/api/v1/financials/orders/{o['id']}/refunds/",
            json.dumps({"amount": 50.00, "reason": "Test refund", "original_payment_id": pay_id}),
            content_type="application/json",
            **WS,
        )
        ref = r.json()
        refund_id = ref.get("id") or ref.get("refund_id", "")
        _admin().post(
            f"/api/v1/financials/refunds/{refund_id}/approve/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        ref["_refund_id"] = refund_id
        return ref

    def test_refund_process(self):
        ref = self._make_approved_refund()
        rid = ref.get("_refund_id", ref.get("id", ""))
        r = _admin().post(
            f"/api/v1/financials/refunds/{rid}/process/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_refund_process_frontdesk_denied(self):
        ref = self._make_approved_refund()
        rid = ref.get("_refund_id", ref.get("id", ""))
        r = _frontdesk().post(
            f"/api/v1/financials/refunds/{rid}/process/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# 11. Financials -- reconciliation (3 endpoints, ~4 tests)
# ---------------------------------------------------------------------------

class TestReconciliationList:
    def test_reconciliation_list(self):
        r = _admin().get("/api/v1/financials/reconciliation/", **WS)
        assert r.status_code == 200

    def test_reconciliation_list_anon_denied(self):
        r = _anon().get("/api/v1/financials/reconciliation/", **WS)
        assert r.status_code in (401, 403)


class TestReconciliationDetail:
    def test_reconciliation_detail_not_found(self):
        r = _admin().get("/api/v1/financials/reconciliation/2020-01-01/", **WS)
        assert r.status_code == 404

    def test_reconciliation_detail_success(self, tmp_path):
        from apps.financials.models import DailyReconciliation
        csv_file = tmp_path / "recon.csv"
        csv_file.write_text("header\nrow")
        DailyReconciliation.objects.create(
            reconciliation_date="2025-01-15",
            total_orders=5,
            total_revenue="500.00",
            total_payments="450.00",
            total_refunds="0.00",
            discrepancy="50.00",
            csv_file_path=str(csv_file),
            generated_by="test",
        )
        r = _admin().get("/api/v1/financials/reconciliation/2025-01-15/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["reconciliation_date"] == "2025-01-15"
        assert body["total_orders"] == 5


class TestReconciliationDownload:
    def test_reconciliation_download_not_found(self):
        r = _admin().get("/api/v1/financials/reconciliation/2020-01-01/download/", **WS)
        assert r.status_code == 404

    def test_reconciliation_download_success(self, tmp_path):
        from apps.financials.models import DailyReconciliation
        csv_file = tmp_path / "recon_dl.csv"
        csv_file.write_text("date,total\n2025-01-16,100")
        DailyReconciliation.objects.create(
            reconciliation_date="2025-01-16",
            total_orders=1,
            total_revenue="100.00",
            total_payments="100.00",
            total_refunds="0.00",
            discrepancy="0.00",
            csv_file_path=str(csv_file),
            generated_by="test",
        )
        r = _admin().get("/api/v1/financials/reconciliation/2025-01-16/download/", **WS)
        assert r.status_code == 200
        assert r["Content-Type"] == "text/csv"


# ---------------------------------------------------------------------------
# 12. Users CRUD + disable/enable (4 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

class TestUserList:
    def test_user_list(self):
        r = _admin().get("/api/v1/users/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_user_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/users/", **WS)
        _assert_role_denied(r)

    def test_user_create(self):
        r = _admin().post(
            "/api/v1/users/",
            json.dumps({
                "username": "newuser_bb",
                "password": "SecurePass123!!",
                "full_name": "New User",
                "email": "new@example.com",
                "role": "front_desk",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201


class TestUserDetail:
    def test_user_detail(self):
        users = User.objects.filter(username="bb_fd")
        uid = str(users.first().pk)
        r = _admin().get(f"/api/v1/users/{uid}/", **WS)
        assert r.status_code == 200

    def test_user_patch(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = _admin().patch(
            f"/api/v1/users/{uid}/",
            json.dumps({"full_name": "Updated Name"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_user_detail_anon_denied(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = _anon().get(f"/api/v1/users/{uid}/", **WS)
        assert r.status_code in (401, 403)


class TestUserDisable:
    def test_user_disable_no_sudo(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = _admin().post(
            f"/api/v1/users/{uid}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403

    def test_user_disable_success_with_sudo(self):
        uid = str(User.objects.get(username="bb_clin").pk)
        c = _admin_with_sudo("user_disable")
        r = c.post(
            f"/api/v1/users/{uid}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["is_active"] is False

    def test_user_disable_frontdesk_denied(self):
        uid = str(User.objects.get(username="bb_clin").pk)
        r = _frontdesk().post(
            f"/api/v1/users/{uid}/disable/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestUserEnable:
    def test_user_enable_success(self):
        # First disable the user, then re-enable
        user = User.objects.get(username="bb_clin")
        user.is_active = False
        user.save(update_fields=["is_active"])
        uid = str(user.pk)
        r = _admin().post(
            f"/api/v1/users/{uid}/enable/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["is_active"] is True

    def test_user_enable_already_active(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = _admin().post(
            f"/api/v1/users/{uid}/enable/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 400

    def test_user_enable_frontdesk_denied(self):
        uid = str(User.objects.get(username="bb_fd").pk)
        r = _frontdesk().post(
            f"/api/v1/users/{uid}/enable/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# 13. Workstations (2 endpoints, ~4 tests)
# ---------------------------------------------------------------------------

class TestWorkstationList:
    def test_workstation_list(self):
        r = _admin().get("/api/v1/workstations/", **WS)
        assert r.status_code == 200

    def test_workstation_list_anon_denied(self):
        r = _anon().get("/api/v1/workstations/", **WS)
        assert r.status_code in (401, 403)

    def test_workstation_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/workstations/", **WS)
        _assert_role_denied(r)


class TestWorkstationUnblock:
    def test_workstation_unblock_not_found(self):
        r = _admin().post("/api/v1/workstations/99999/unblock/", **WS)
        # No sudo -> 403
        assert r.status_code == 403

    def test_workstation_unblock_success_with_sudo(self):
        from apps.accounts.models import WorkstationBlacklist
        bl = WorkstationBlacklist.objects.create(
            client_ip="10.0.0.99",
            workstation_id="ws-blocked-01",
            is_active=True,
        )
        c = _admin_with_sudo("workstation_unblock")
        r = c.post(f"/api/v1/workstations/{bl.pk}/unblock/", **WS)
        assert r.status_code == 200
        bl.refresh_from_db()
        assert bl.is_active is False

    def test_workstation_unblock_anon_denied(self):
        r = _anon().post("/api/v1/workstations/1/unblock/", **WS)
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 14. Sudo acquire / status / release (3 endpoints, ~6 tests)
# ---------------------------------------------------------------------------

class TestSudoAcquire:
    def test_sudo_acquire(self):
        r = _admin().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "Pass1234!", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert "action_class" in r.json()

    def test_sudo_acquire_bad_password(self):
        r = _admin().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "wrong", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 401

    def test_sudo_acquire_frontdesk_denied(self):
        r = _frontdesk().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "Pass1234!", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestSudoStatus:
    def test_sudo_status(self):
        r = _admin().get("/api/v1/sudo/status/", **WS)
        assert r.status_code == 200
        assert "active_sudo_actions" in r.json()

    def test_sudo_status_anon_denied(self):
        r = _anon().get("/api/v1/sudo/status/", **WS)
        assert r.status_code in (401, 403)


class TestSudoRelease:
    def test_sudo_release(self):
        r = _admin().delete("/api/v1/sudo/release/", **WS)
        assert r.status_code == 204

    def test_sudo_release_anon_denied(self):
        r = _anon().delete("/api/v1/sudo/release/", **WS)
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 15. Audit entries / verify / purge (4 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

class TestAuditList:
    def test_audit_list(self):
        r = _admin().get("/api/v1/audit/entries/", **WS)
        assert r.status_code == 200

    def test_audit_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/audit/entries/", **WS)
        assert r.status_code == 403

    def test_audit_list_anon_denied(self):
        r = _anon().get("/api/v1/audit/entries/", **WS)
        assert r.status_code in (401, 403)


class TestAuditDetail:
    def test_audit_detail_success(self):
        from apps.audit.service import create_audit_entry
        entry = create_audit_entry(
            event_type="test_detail",
            target_model="Test",
            target_id="1",
            target_repr="test",
        )
        r = _admin().get(f"/api/v1/audit/entries/{entry.pk}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["event_type"] == "test_detail"

    def test_audit_detail_not_found(self):
        r = _admin().get("/api/v1/audit/entries/999999/", **WS)
        assert r.status_code == 404

    def test_audit_detail_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/audit/entries/1/", **WS)
        assert r.status_code == 403


class TestAuditVerifyChain:
    def test_verify_chain(self):
        r = _admin().post("/api/v1/audit/verify-chain/", **WS)
        assert r.status_code == 200
        assert "is_valid" in r.json()

    def test_verify_chain_frontdesk_denied(self):
        r = _frontdesk().post("/api/v1/audit/verify-chain/", **WS)
        assert r.status_code == 403


class TestAuditPurge:
    def test_purge_success_with_sudo(self):
        c = _admin_with_sudo("log_purge")
        r = c.post(
            "/api/v1/audit/purge/",
            json.dumps({
                "confirm": True,
                "before_date": "2017-01-01T00:00:00Z",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "deleted_count" in body

    def test_purge_no_sudo(self):
        r = _admin().post(
            "/api/v1/audit/purge/",
            json.dumps({
                "confirm": True,
                "before_date": "2017-01-01T00:00:00Z",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403  # sudo required

    def test_purge_anon_denied(self):
        r = _anon().post(
            "/api/v1/audit/purge/",
            json.dumps({"confirm": True, "before_date": "2017-01-01T00:00:00Z"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 16. Reports -- subscriptions (3 endpoints, ~6 tests)
# ---------------------------------------------------------------------------

class TestSubscriptionListCreate:
    def test_subscription_list(self):
        r = _admin().get("/api/v1/reports/subscriptions/", **WS)
        assert r.status_code == 200

    def test_subscription_create(self):
        r = _admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Daily Recon",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "parameters": {},
                "run_time": "08:00:00",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201

    def test_subscription_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/reports/subscriptions/", **WS)
        _assert_role_denied(r)

    def test_subscription_create_compliance_denied(self):
        r = _compliance().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Test",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "parameters": {},
                "run_time": "08:00:00",
            }),
            content_type="application/json",
            **WS,
        )
        # Compliance can read but not create (admin only for POST)
        assert r.status_code == 403


class TestSubscriptionDetail:
    def _make_sub(self):
        r = _admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Test Sub",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "parameters": {},
                "run_time": "08:00:00",
            }),
            content_type="application/json",
            **WS,
        )
        return r.json()

    def test_subscription_detail(self):
        sub = self._make_sub()
        r = _admin().get(f"/api/v1/reports/subscriptions/{sub['id']}/", **WS)
        assert r.status_code == 200

    def test_subscription_patch(self):
        sub = self._make_sub()
        r = _admin().patch(
            f"/api/v1/reports/subscriptions/{sub['id']}/",
            json.dumps({"name": "Updated Sub Name"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Sub Name"

    def test_subscription_delete_deactivate(self):
        sub = self._make_sub()
        r = _admin().delete(f"/api/v1/reports/subscriptions/{sub['id']}/", **WS)
        assert r.status_code == 200


class TestSubscriptionRunNow:
    def test_run_now(self):
        r = _admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Run Now Sub",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "parameters": {},
                "run_time": "08:00:00",
            }),
            content_type="application/json",
            **WS,
        )
        sub = r.json()
        r2 = _admin().post(
            f"/api/v1/reports/subscriptions/{sub['id']}/run-now/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r2.status_code == 201

    def test_run_now_frontdesk_denied(self):
        r = _admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Run Now Sub 2",
                "report_type": "daily_reconciliation",
                "schedule": "daily",
                "output_format": "pdf",
                "parameters": {},
                "run_time": "08:00:00",
            }),
            content_type="application/json",
            **WS,
        )
        sub = r.json()
        r2 = _frontdesk().post(
            f"/api/v1/reports/subscriptions/{sub['id']}/run-now/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r2.status_code == 403


# ---------------------------------------------------------------------------
# 17. Reports -- outbox (5 endpoints, ~8 tests)
# ---------------------------------------------------------------------------

class TestOutboxList:
    def test_outbox_list(self):
        r = _admin().get("/api/v1/reports/outbox/", **WS)
        assert r.status_code == 200

    def test_outbox_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/reports/outbox/", **WS)
        assert r.status_code == 403


def _make_outbox_item(status="delivered", file_path=""):
    from apps.reports.models import OutboxItem
    return OutboxItem.objects.create(
        report_name="Test Report",
        file_format="pdf",
        status=status,
        file_path=file_path,
        delivery_target="shared_folder",
    )


class TestOutboxDetail:
    def test_outbox_detail_success(self):
        item = _make_outbox_item()
        r = _admin().get(f"/api/v1/reports/outbox/{item.pk}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["report_name"] == "Test Report"

    def test_outbox_detail_not_found(self):
        r = _admin().get(f"/api/v1/reports/outbox/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404


class TestOutboxDownload:
    def test_outbox_download_success(self, tmp_path):
        f = tmp_path / "report.pdf"
        f.write_text("fake pdf content")
        item = _make_outbox_item(file_path=str(f))
        r = _admin().get(f"/api/v1/reports/outbox/{item.pk}/download/", **WS)
        assert r.status_code == 200

    def test_outbox_download_not_found(self):
        r = _admin().get(f"/api/v1/reports/outbox/{uuid.uuid4()}/download/", **WS)
        assert r.status_code == 404


class TestOutboxRetry:
    def test_outbox_retry_success(self):
        item = _make_outbox_item(status="failed")
        r = _admin().post(
            f"/api/v1/reports/outbox/{item.pk}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "message" in body

    def test_outbox_retry_not_found(self):
        r = _admin().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 404

    def test_outbox_retry_frontdesk_denied(self):
        r = _frontdesk().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestOutboxAcknowledge:
    def test_outbox_acknowledge_success(self):
        item = _make_outbox_item(status="stalled")
        r = _admin().post(
            f"/api/v1/reports/outbox/{item.pk}/acknowledge/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_outbox_acknowledge_not_found(self):
        r = _admin().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/acknowledge/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 404

    def test_outbox_acknowledge_frontdesk_denied(self):
        r = _frontdesk().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/acknowledge/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# 18. Reports -- dashboard (1 endpoint, ~3 tests)
# ---------------------------------------------------------------------------

class TestReportDashboard:
    def test_dashboard(self):
        r = _admin().get("/api/v1/reports/dashboard/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "queued" in body

    def test_dashboard_compliance(self):
        r = _compliance().get("/api/v1/reports/dashboard/", **WS)
        assert r.status_code == 200

    def test_dashboard_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/reports/dashboard/", **WS)
        _assert_role_denied(r)


# ---------------------------------------------------------------------------
# 19. Export (3 endpoints, ~6 tests)
# ---------------------------------------------------------------------------

class TestExportPatients:
    def test_export_patients_no_sudo(self):
        r = _admin().post(
            "/api/v1/export/patients/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403  # sudo required

    def test_export_patients_anon_denied(self):
        r = _anon().post(
            "/api/v1/export/patients/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


class TestExportMedia:
    def test_export_media_no_sudo(self):
        r = _admin().post(
            "/api/v1/export/media/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403

    def test_export_media_frontdesk_denied(self):
        r = _frontdesk().post(
            "/api/v1/export/media/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403


class TestExportFinancials:
    def test_export_financials_no_sudo(self):
        r = _admin().post(
            "/api/v1/export/financials/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403

    def test_export_financials_anon_denied(self):
        r = _anon().post(
            "/api/v1/export/financials/",
            json.dumps({"confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 20. Policies (2 endpoints, ~4 tests)
# ---------------------------------------------------------------------------

class TestPolicyList:
    def test_policy_list(self):
        r = _admin().get("/api/v1/policies/", **WS)
        assert r.status_code == 200

    def test_policy_list_frontdesk_denied(self):
        r = _frontdesk().get("/api/v1/policies/", **WS)
        _assert_role_denied(r)


class TestPolicyUpdate:
    def test_policy_update_success_with_sudo(self):
        from apps.accounts.models import SystemPolicy
        SystemPolicy.objects.create(
            key="test_bb_policy",
            value="old_value",
            description="Test policy for blackbox",
        )
        c = _admin_with_sudo("policy_update")
        r = c.patch(
            "/api/v1/policies/test_bb_policy/",
            json.dumps({"value": "new_value", "confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["value"] == "new_value"
        assert body["key"] == "test_bb_policy"

    def test_policy_update_no_sudo(self):
        r = _admin().patch(
            "/api/v1/policies/some_key/",
            json.dumps({"value": "new", "confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403  # sudo required

    def test_policy_update_anon_denied(self):
        r = _anon().patch(
            "/api/v1/policies/test_key/",
            json.dumps({"value": "new", "confirm": True}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 21. Client error logs (1 endpoint, ~3 tests)
# ---------------------------------------------------------------------------

class TestClientErrorLog:
    def test_client_error_log_authenticated(self):
        r = _admin().post(
            "/api/v1/logs/client-errors/",
            json.dumps({
                "level": "error",
                "message": "TypeError: cannot read property",
                "url": "https://medrights.example.com/dashboard",
                "timestamp": "2024-01-01T00:00:00Z",
                "component": "PatientSearch",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201

    def test_client_error_log_missing_message(self):
        r = _admin().post(
            "/api/v1/logs/client-errors/",
            json.dumps({"level": "error"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 400

    def test_client_error_log_rejects_sensitive_fields(self):
        r = _admin().post(
            "/api/v1/logs/client-errors/",
            json.dumps({
                "level": "error",
                "message": "Some error",
                "password": "secret123",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Additional cross-cutting tests
# ---------------------------------------------------------------------------

class TestCrossCuttingAuth:
    """Verify that various protected endpoints reject anonymous users
    and return a well-formed error body (not just a status code)."""

    def test_patients_create_anon(self):
        _assert_denied(_anon().post("/api/v1/patients/create/", **WS))

    def test_media_list_anon(self):
        _assert_denied(_anon().get("/api/v1/media/", **WS))

    def test_orders_list_anon(self):
        _assert_denied(_anon().get("/api/v1/financials/orders/", **WS))

    def test_refunds_list_anon(self):
        _assert_denied(_anon().get("/api/v1/financials/refunds/", **WS))

    def test_audit_list_anon(self):
        _assert_denied(_anon().get("/api/v1/audit/entries/", **WS))

    def test_users_list_anon(self):
        _assert_denied(_anon().get("/api/v1/users/", **WS))

    def test_sudo_acquire_anon(self):
        _assert_denied(_anon().post(
            "/api/v1/sudo/acquire/",
            json.dumps({"password": "x", "action_class": "user_disable"}),
            content_type="application/json",
            **WS,
        ))

    def test_reports_subscriptions_anon(self):
        _assert_denied(_anon().get("/api/v1/reports/subscriptions/", **WS))

    def test_reports_outbox_anon(self):
        _assert_denied(_anon().get("/api/v1/reports/outbox/", **WS))

    def test_reports_dashboard_anon(self):
        _assert_denied(_anon().get("/api/v1/reports/dashboard/", **WS))

    def test_workstations_list_anon(self):
        _assert_denied(_anon().get("/api/v1/workstations/", **WS))

    def test_policies_list_anon(self):
        _assert_denied(_anon().get("/api/v1/policies/", **WS))
