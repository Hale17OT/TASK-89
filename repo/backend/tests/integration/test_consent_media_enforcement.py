"""Integration tests for consent-enforced media flows.

Covers: upload with consent, download with consent, attach-patient with
consent — across revoked, expired, future-effective, wrong-scope, and
wrong-patient consent states.

These tests create MediaAsset records via the ORM (not the upload endpoint)
to isolate the consent-enforcement logic from the file-processing path.
"""
import os
import uuid
from datetime import date, timedelta

import pytest
from django.conf import settings

from apps.accounts.models import User
from apps.consent.models import Consent, ConsentScope
from apps.media_engine.models import MediaAsset

pytestmark = pytest.mark.django_db


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_patient(client):
    """Create a patient via the API (encryption handled by the endpoint)."""
    resp = client.post("/api/v1/patients/create/", {
        "mrn": f"MRN-{uuid.uuid4().hex[:6]}",
        "first_name": "Test",
        "last_name": "Patient",
        "date_of_birth": "1990-01-01",
        "gender": "M",
    }, format="json")
    assert resp.status_code == 201, f"Patient creation failed: {resp.data}"
    return resp.data["id"]


def _make_consent(patient_id, user, *, effective_date=None, expiration_date=None,
                   is_revoked=False, scope_type="media_use",
                   scope_value="capture_storage"):
    """Create a Consent + ConsentScope."""
    consent = Consent.objects.create(
        patient_id=patient_id,
        purpose="Test consent",
        granted_by=user,
        effective_date=effective_date or (date.today() - timedelta(days=30)),
        expiration_date=expiration_date or (date.today() + timedelta(days=365)),
        is_revoked=is_revoked,
    )
    if scope_type:
        ConsentScope.objects.create(
            consent=consent,
            scope_type=scope_type,
            scope_value=scope_value,
        )
    return consent


def _make_media_asset(user, *, consent=None, patient_id=None):
    """Create a MediaAsset via ORM (no file I/O)."""
    storage = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    rel_path = f"media/test/{uuid.uuid4().hex}.png"
    abs_path = os.path.join(storage, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    return MediaAsset.objects.create(
        patient_id=patient_id,
        consent=consent,
        original_file=rel_path,
        original_filename="test.png",
        mime_type="image/png",
        file_size_bytes=108,
        pixel_hash=uuid.uuid4().hex,
        file_hash=uuid.uuid4().hex,
        originality_status="original",
        uploaded_by=user,
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="consent_test_user", password="Pass123!!", role="admin",
    )


@pytest.fixture
def client(user):
    from rest_framework.test import APIClient
    c = APIClient()
    c.force_authenticate(user=user)
    c.defaults["HTTP_X_WORKSTATION_ID"] = "ws-consent-test"
    return c


@pytest.fixture(autouse=True)
def _ensure_storage():
    import shutil
    storage = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    os.makedirs(storage, exist_ok=True)
    yield
    if os.path.isdir(os.path.join(storage, "media", "test")):
        shutil.rmtree(os.path.join(storage, "media", "test"), ignore_errors=True)


# ── Download tests ──────────────────────────────────────────────────────

class TestDownloadConsentEnforcement:
    """GET /api/v1/media/{id}/download/ must reject invalid consent."""

    def test_download_with_active_consent_succeeds(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user)
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 200

    def test_download_with_revoked_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user, is_revoked=True)
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "revoked" in resp.data["message"].lower()

    def test_download_with_expired_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() - timedelta(days=365),
            expiration_date=date.today() - timedelta(days=1),
        )
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "expired" in resp.data["message"].lower()

    def test_download_with_future_effective_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() + timedelta(days=30),
            expiration_date=date.today() + timedelta(days=365),
        )
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "not yet effective" in resp.data["message"].lower()

    def test_download_with_wrong_scope_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            scope_type="action",
            scope_value="data_sharing",
        )
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "media_use" in resp.data["message"].lower()

    def test_download_with_no_scopes_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user, scope_type=None)
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"

    def test_download_with_wrong_scope_value_rejected(self, client, user):
        """media_use scope exists but value is not capture_storage."""
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            scope_type="media_use",
            scope_value="marketing_only",
        )
        asset = _make_media_asset(user, consent=consent, patient_id=pid)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "capture_storage" in resp.data["message"].lower()

    def test_download_without_consent_succeeds(self, client, user):
        """Media with no linked consent should still be downloadable."""
        asset = _make_media_asset(user)

        resp = client.get(f"/api/v1/media/{asset.pk}/download/")
        assert resp.status_code == 200


# ── Attach-patient tests ────────────────────────────────────────────────

class TestAttachPatientConsentEnforcement:
    """POST /api/v1/media/{id}/attach-patient/ must respect consent."""

    def test_attach_with_active_consent_succeeds(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user)
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 200

    def test_attach_with_revoked_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user, is_revoked=True)
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"

    def test_attach_with_expired_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() - timedelta(days=365),
            expiration_date=date.today() - timedelta(days=1),
        )
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"

    def test_attach_with_future_effective_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() + timedelta(days=30),
            expiration_date=date.today() + timedelta(days=365),
        )
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "not yet effective" in resp.data["message"].lower()

    def test_attach_with_wrong_patient_rejected(self, client, user):
        pid_a = _make_patient(client)
        pid_b = _make_patient(client)
        consent = _make_consent(pid_a, user)  # consent belongs to patient_a
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid_b},  # attaching to patient_b
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"
        assert "patient" in resp.data["message"].lower()

    def test_attach_with_wrong_scope_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            scope_type="action",
            scope_value="data_sharing",
        )
        asset = _make_media_asset(user, consent=consent)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["error"] == "consent_invalid"

    def test_attach_without_consent_succeeds(self, client, user):
        """Media without consent should still be attachable."""
        pid = _make_patient(client)
        asset = _make_media_asset(user)

        resp = client.post(
            f"/api/v1/media/{asset.pk}/attach-patient/",
            {"patient_id": pid},
            format="json",
        )
        assert resp.status_code == 200


# ── Upload with consent_id tests ────────────────────────────────────────

class TestUploadConsentValidation:
    """POST /api/v1/media/upload/ with consent_id validates the consent.

    These tests use multipart upload with a minimal PNG file.  If the
    test environment cannot process images, they will be skipped.
    """

    @staticmethod
    def _minimal_png():
        """Return a minimal valid PNG file-like object."""
        import io
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")
        img = Image.new("RGB", (2, 2), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "upload_test.png"
        return buf

    def test_upload_with_revoked_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(pid, user, is_revoked=True)
        img = self._minimal_png()

        resp = client.post(
            "/api/v1/media/upload/",
            {"file": img, "consent_id": str(consent.pk)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert "consent_id" in resp.data or "revoked" in str(resp.data).lower()

    def test_upload_with_expired_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() - timedelta(days=365),
            expiration_date=date.today() - timedelta(days=1),
        )
        img = self._minimal_png()

        resp = client.post(
            "/api/v1/media/upload/",
            {"file": img, "consent_id": str(consent.pk)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert "consent_id" in resp.data or "expired" in str(resp.data).lower()

    def test_upload_with_wrong_scope_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            scope_type="action",
            scope_value="data_sharing",
        )
        img = self._minimal_png()

        resp = client.post(
            "/api/v1/media/upload/",
            {"file": img, "consent_id": str(consent.pk)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert "consent_id" in resp.data or "media_use" in str(resp.data).lower()

    def test_upload_with_future_effective_consent_rejected(self, client, user):
        pid = _make_patient(client)
        consent = _make_consent(
            pid, user,
            effective_date=date.today() + timedelta(days=30),
            expiration_date=date.today() + timedelta(days=365),
        )
        img = self._minimal_png()

        resp = client.post(
            "/api/v1/media/upload/",
            {"file": img, "consent_id": str(consent.pk)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert "consent_id" in resp.data or "not yet effective" in str(resp.data).lower()

    def test_upload_with_wrong_patient_consent_rejected(self, client, user):
        """Upload with consent_id + patient_id where consent belongs to a different patient."""
        pid_a = _make_patient(client)
        pid_b = _make_patient(client)
        consent = _make_consent(pid_a, user)  # consent belongs to patient_a
        img = self._minimal_png()

        resp = client.post(
            "/api/v1/media/upload/",
            {"file": img, "consent_id": str(consent.pk), "patient_id": pid_b},
            format="multipart",
        )
        assert resp.status_code == 400
        assert "consent_id" in resp.data or "patient" in str(resp.data).lower()
