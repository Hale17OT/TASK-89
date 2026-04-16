"""Black-box tests: Patients CRUD, Break-Glass, Consents."""
import json
import uuid

from .conftest import WS, admin, frontdesk, clinician, anon, assert_denied, create_patient


class TestPatientCreate:
    def test_create_patient_admin(self):
        p = create_patient()
        assert "id" in p
        assert "name" in p

    def test_create_patient_frontdesk(self):
        p = create_patient(client_fn=frontdesk)
        assert "id" in p

    def test_create_patient_clinician_denied(self):
        r = clinician().post(
            "/api/v1/patients/create/",
            json.dumps({
                "mrn": "MRN-X", "ssn": "999", "first_name": "A", "last_name": "B",
                "date_of_birth": "2000-01-01", "gender": "M",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 403
        assert "detail" in r.json() or "error" in r.json()


class TestPatientSearch:
    def test_search_patients(self):
        p = create_patient()
        r = admin().get("/api/v1/patients/?q=123456789", **WS)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_search_missing_q(self):
        r = admin().get("/api/v1/patients/", **WS)
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "missing_query"

    def test_search_anon_denied(self):
        assert_denied(anon().get("/api/v1/patients/?q=test", **WS))


class TestPatientDetail:
    def test_detail(self):
        p = create_patient()
        r = admin().get(f"/api/v1/patients/{p['id']}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == p["id"]

    def test_detail_not_found(self):
        r = admin().get(f"/api/v1/patients/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"


class TestBreakGlass:
    def test_break_glass_success(self):
        p = create_patient()
        r = admin().post(
            f"/api/v1/patients/{p['id']}/break-glass/",
            json.dumps({
                "justification": "Emergency patient treatment required immediately",
                "justification_category": "treatment",
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201
        body = r.json()
        assert "break_glass_log_id" in body
        assert "patient" in body

    def test_break_glass_anon_denied(self):
        p = create_patient()
        assert_denied(anon().post(
            f"/api/v1/patients/{p['id']}/break-glass/",
            json.dumps({
                "justification": "Emergency patient treatment required immediately",
                "justification_category": "treatment",
            }),
            content_type="application/json",
            **WS,
        ))


class TestConsentCreate:
    def test_consent_create(self):
        p = create_patient()
        r = admin().post(
            f"/api/v1/patients/{p['id']}/consents/",
            json.dumps({
                "purpose": "Media capture and storage",
                "effective_date": "2024-01-01",
                "expiration_date": "2025-12-31",
                "scopes": [
                    {"scope_type": "media_use", "scope_value": "capture_storage"},
                ],
            }),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["is_revoked"] is False

    def test_consent_list(self):
        p = create_patient()
        r = admin().get(f"/api/v1/patients/{p['id']}/consents/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_consent_list_anon_denied(self):
        p = create_patient()
        assert_denied(anon().get(f"/api/v1/patients/{p['id']}/consents/", **WS))
