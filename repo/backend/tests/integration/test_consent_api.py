"""Integration tests for the Consent API endpoints."""
from datetime import date, timedelta

import pytest


pytestmark = pytest.mark.django_db


def _consent_url(patient_id, suffix=""):
    return f"/api/v1/patients/{patient_id}/consents/{suffix}"


def _create_consent(client, patient_id, **overrides):
    """Helper to create a consent and return the response."""
    payload = {
        "purpose": "Treatment consent",
        "effective_date": str(date.today()),
        "expiration_date": str(date.today() + timedelta(days=365)),
        "physical_copy_on_file": False,
    }
    payload.update(overrides)
    return client.post(
        _consent_url(patient_id),
        payload,
        format="json",
    )


# ------------------------------------------------------------------
# Create
# ------------------------------------------------------------------

class TestConsentCreate:
    def test_create_consent(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        resp = _create_consent(auth_client, pid)
        assert resp.status_code == 201
        assert resp.data["purpose"] == "Treatment consent"
        assert resp.data["is_revoked"] is False

    def test_create_consent_invalid_dates(self, auth_client, sample_patient):
        """Expiration before effective date should be rejected."""
        pid = sample_patient["id"]
        resp = _create_consent(
            auth_client,
            pid,
            effective_date=str(date.today()),
            expiration_date=str(date.today() - timedelta(days=1)),
        )
        # The custom exception handler returns 400 for validation errors
        assert resp.status_code == 400


# ------------------------------------------------------------------
# List
# ------------------------------------------------------------------

class TestConsentList:
    def test_list_consents(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        _create_consent(auth_client, pid, purpose="Consent A")
        _create_consent(auth_client, pid, purpose="Consent B")

        resp = auth_client.get(_consent_url(pid, ""))
        assert resp.status_code == 200
        assert resp.data["count"] == 2
        assert len(resp.data["results"]) == 2


# ------------------------------------------------------------------
# Revoke
# ------------------------------------------------------------------

class TestConsentRevoke:
    def test_revoke_consent(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        create_resp = _create_consent(auth_client, pid)
        consent_id = create_resp.data["id"]

        revoke_resp = auth_client.post(
            _consent_url(pid, f"{consent_id}/revoke/"),
            {"reason": "Patient requested revocation"},
            format="json",
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.data["is_revoked"] is True
        assert revoke_resp.data["revocation_reason"] == "Patient requested revocation"

    def test_revoke_already_revoked(self, auth_client, sample_patient):
        """Revoking an already-revoked consent should return 400 (ConflictError)."""
        pid = sample_patient["id"]
        create_resp = _create_consent(auth_client, pid)
        consent_id = create_resp.data["id"]

        # Revoke once
        auth_client.post(
            _consent_url(pid, f"{consent_id}/revoke/"),
            {"reason": "First revocation"},
            format="json",
        )
        # Revoke again
        resp = auth_client.post(
            _consent_url(pid, f"{consent_id}/revoke/"),
            {"reason": "Second attempt"},
            format="json",
        )
        assert resp.status_code == 400

    def test_revoke_physical_copy_warning(self, auth_client, sample_patient):
        """When physical_copy_on_file=True, revocation without acknowledgment
        should be rejected."""
        pid = sample_patient["id"]
        create_resp = _create_consent(
            auth_client, pid, physical_copy_on_file=True,
        )
        consent_id = create_resp.data["id"]

        # Without acknowledgment
        resp = auth_client.post(
            _consent_url(pid, f"{consent_id}/revoke/"),
            {"reason": "Revoke physical copy consent"},
            format="json",
        )
        assert resp.status_code == 400

        # With acknowledgment
        resp2 = auth_client.post(
            _consent_url(pid, f"{consent_id}/revoke/"),
            {
                "reason": "Revoke physical copy consent",
                "physical_copy_warning_acknowledged": True,
            },
            format="json",
        )
        assert resp2.status_code == 200
        assert resp2.data["is_revoked"] is True
