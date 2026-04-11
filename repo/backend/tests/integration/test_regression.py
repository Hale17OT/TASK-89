"""Regression tests for audit-driven fixes.

Covers: consent-filtered exports, attach-patient flow, infringement->disputed
lifecycle, authenticated workstation-ID enforcement, and delivery-target routing.
"""
import io
import os
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consent.models import Consent, ConsentScope
from apps.media_engine.models import InfringementReport, MediaAsset


pytestmark = pytest.mark.django_db


# ── helpers ───────────────────────────────────────────────────────────────

def _create_test_image():
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "test.png"
    return buf


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(username="reg_admin", password="Pass123!!", role="admin")
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-reg-test"
    client.login(username="reg_admin", password="Pass123!!")
    return client, user


@pytest.fixture
def frontdesk_client(db):
    user = User.objects.create_user(username="reg_fd", password="Pass123!!", role="front_desk")
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-reg-test-fd"
    return client, user


@pytest.fixture
def clinician_client(db):
    user = User.objects.create_user(username="reg_clin", password="Pass123!!", role="clinician")
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-reg-test-clin"
    return client, user


def _create_patient(client):
    resp = client.post("/api/v1/patients/create/", {
        "mrn": "REG001", "first_name": "Test", "last_name": "Patient",
        "date_of_birth": "1990-01-01", "gender": "M",
    }, format="json")
    assert resp.status_code == 201
    return resp.data["id"]


def _create_consent_with_scope(user, patient_id, scope_type, scope_value):
    consent = Consent.objects.create(
        patient_id=patient_id,
        purpose="Test consent",
        granted_by=user,
        effective_date=date.today() - timedelta(days=1),
        expiration_date=date.today() + timedelta(days=365),
    )
    ConsentScope.objects.create(
        consent=consent, scope_type=scope_type, scope_value=scope_value,
    )
    return consent


def _acquire_sudo(client, password="Pass123!!"):
    return client.post("/api/v1/sudo/acquire/", {
        "password": password, "action_class": "bulk_export",
    })


# ── Test: export consent-scope filtering ──────────────────────────────────

class TestExportConsentScoping:
    def test_patient_export_requires_data_sharing_scope(self, admin_client):
        client, user = admin_client
        pid = _create_patient(client)
        # Consent without data_sharing scope
        _create_consent_with_scope(user, pid, "media_use", "capture_storage")
        _acquire_sudo(client)
        resp = client.post("/api/v1/export/patients/", {"confirm": True}, format="json")
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        # Patient should NOT be in export (no data_sharing scope)
        assert pid not in content

    def test_patient_export_includes_with_correct_scope(self, admin_client):
        client, user = admin_client
        pid = _create_patient(client)
        _create_consent_with_scope(user, pid, "action", "data_sharing")
        _acquire_sudo(client)
        resp = client.post("/api/v1/export/patients/", {"confirm": True}, format="json")
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert pid in content


# ── Test: attach-patient flow ─────────────────────────────────────────────

class TestAttachPatientFlow:
    def test_clinician_can_attach_media_to_patient(self, clinician_client, admin_client):
        client, user = clinician_client
        admin_c, _ = admin_client
        pid = _create_patient(admin_c)
        # Upload media
        img = _create_test_image()
        resp = client.post("/api/v1/media/upload/", {"file": img}, format="multipart")
        assert resp.status_code == 201
        media_id = resp.data["id"]
        # Attach to patient
        resp = client.post(f"/api/v1/media/{media_id}/attach-patient/", {
            "patient_id": pid,
        }, format="json")
        assert resp.status_code == 200
        assert resp.data.get("patient_id") == pid or "attached" in str(resp.data).lower()


# ── Test: infringement -> disputed lifecycle ──────────────────────────────

class TestInfringementDisputedLifecycle:
    def test_infringement_creation_sets_media_to_disputed(self, admin_client):
        client, user = admin_client
        # Upload media
        img = _create_test_image()
        resp = client.post("/api/v1/media/upload/", {"file": img}, format="multipart")
        assert resp.status_code == 201
        media_id = resp.data["id"]
        # Create infringement (need compliance role)
        compliance_user = User.objects.create_user(
            username="reg_comp", password="Pass123!!", role="compliance")
        comp_client = APIClient()
        comp_client.force_authenticate(compliance_user)
        comp_client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-comp"
        resp = comp_client.post("/api/v1/media/infringement/", {
            "media_asset_id": media_id,
            "notes": "This is a test infringement report for regression testing.",
            "reference": "internal-review-2026-001",
        }, format="json")
        assert resp.status_code == 201
        # Verify media is now disputed
        asset = MediaAsset.objects.get(pk=media_id)
        assert asset.originality_status == "disputed"


# ── Test: authenticated requests require workstation ID ───────────────────

class TestWorkstationIDEnforcement:
    def test_authenticated_request_without_workstation_id_rejected(self, db):
        """Session-authenticated user without X-Workstation-ID gets 400."""
        user = User.objects.create_user(username="reg_no_ws", password="Pass123!!", role="front_desk")
        client = APIClient()
        # Use login() to create a real Django session (not force_authenticate
        # which is DRF-specific and invisible to Django middleware).
        client.login(username="reg_no_ws", password="Pass123!!")
        # Do NOT set X-Workstation-ID header
        resp = client.get("/api/v1/patients/", {"q": "test"})
        assert resp.status_code == 400
        data = resp.json()
        assert "workstation" in data.get("error", "").lower() or \
               "workstation" in data.get("message", "").lower()

    def test_unauthenticated_health_check_works_without_workstation_id(self, db):
        client = APIClient()
        resp = client.get("/api/v1/health/")
        # Health check is AllowAny and unauthenticated, should work
        assert resp.status_code in (200, 503)


# ── Test: delivery-target routing ─────────────────────────────────────────

class TestDeliveryTargetRouting:
    """Verify that deliver_outbox_item routes files to the correct destination
    based on delivery_target (shared_folder vs print_queue)."""

    def _create_outbox_item(self, tmp_path, delivery_target, delivery_path=""):
        from apps.reports.models import OutboxItem, OutboxStatus, ReportSubscription
        from apps.accounts.models import User

        user = User.objects.create_user(
            username=f"del_{delivery_target[:5]}_{id(self)}",
            password="P!", role="admin",
        )
        sub = ReportSubscription.objects.create(
            name="Del Test", report_type="financial_summary",
            schedule="daily", output_format="pdf",
            run_time="08:00:00", created_by=user,
        )
        item = OutboxItem.objects.create(
            subscription=sub,
            report_name="Delivery Test",
            file_format="pdf",
            status=OutboxStatus.QUEUED,
            delivery_target=delivery_target,
            delivery_target_path=delivery_path,
        )
        # Create a fake pending file
        pending_dir = tmp_path / "outbox" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        fake_file = pending_dir / f"{item.pk}.pdf"
        fake_file.write_text("fake PDF content")
        item.file_path = f"outbox/pending/{item.pk}.pdf"
        item.save(update_fields=["file_path"])
        return item

    def test_shared_folder_delivery_to_default_path(self, tmp_path):
        item = self._create_outbox_item(tmp_path, "shared_folder")
        with patch("apps.reports.tasks._storage_root", return_value=str(tmp_path)):
            from apps.reports.tasks import deliver_outbox_item
            deliver_outbox_item(str(item.pk))
        item.refresh_from_db()
        assert item.status == "delivered"
        delivered_file = tmp_path / "outbox" / "delivered" / f"{item.pk}.pdf"
        assert delivered_file.exists()

    def test_shared_folder_delivery_to_custom_path(self, tmp_path):
        custom_dir = str(tmp_path / "custom_share")
        item = self._create_outbox_item(tmp_path, "shared_folder", custom_dir)
        with patch("apps.reports.tasks._storage_root", return_value=str(tmp_path)):
            from apps.reports.tasks import deliver_outbox_item
            deliver_outbox_item(str(item.pk))
        item.refresh_from_db()
        assert item.status == "delivered"
        assert (tmp_path / "custom_share" / f"{item.pk}.pdf").exists()

    def test_print_queue_delivery_to_default_path(self, tmp_path):
        item = self._create_outbox_item(tmp_path, "print_queue")
        with patch("apps.reports.tasks._storage_root", return_value=str(tmp_path)):
            from apps.reports.tasks import deliver_outbox_item
            deliver_outbox_item(str(item.pk))
        item.refresh_from_db()
        assert item.status == "delivered"
        queue_file = tmp_path / "outbox" / "print_queue" / f"{item.pk}.pdf"
        assert queue_file.exists()

    def test_print_queue_delivery_to_custom_path(self, tmp_path):
        custom_queue = str(tmp_path / "my_printer_spool")
        item = self._create_outbox_item(tmp_path, "print_queue", custom_queue)
        with patch("apps.reports.tasks._storage_root", return_value=str(tmp_path)):
            from apps.reports.tasks import deliver_outbox_item
            deliver_outbox_item(str(item.pk))
        item.refresh_from_db()
        assert item.status == "delivered"
        assert (tmp_path / "my_printer_spool" / f"{item.pk}.pdf").exists()

    def test_delivery_failure_increments_retry(self, tmp_path):
        item = self._create_outbox_item(tmp_path, "shared_folder", "/nonexistent/readonly/path")
        # Remove the pending file so delivery fails
        pending = tmp_path / "outbox" / "pending" / f"{item.pk}.pdf"
        pending.unlink()
        with patch("apps.reports.tasks._storage_root", return_value=str(tmp_path)):
            try:
                from apps.reports.tasks import deliver_outbox_item
                deliver_outbox_item(str(item.pk))
            except Exception:
                pass
        item.refresh_from_db()
        assert item.status == "failed"
        assert item.retry_count >= 1
