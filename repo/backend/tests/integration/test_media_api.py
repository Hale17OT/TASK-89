"""Integration tests for the Media & Originality Engine API endpoints."""
import io
import os
import shutil

import pytest
from django.conf import settings
from PIL import Image

from apps.media_engine.models import Citation, InfringementReport, MediaAsset


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _create_test_image(color="red", size=(10, 10), fmt="PNG"):
    """Create a minimal in-memory PNG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    buf.name = "test.png"
    return buf


@pytest.fixture(autouse=True)
def _ensure_storage():
    """Ensure the test storage directory exists and is cleaned up."""
    os.makedirs(settings.MEDRIGHTS_STORAGE_ROOT, exist_ok=True)
    yield
    if os.path.isdir(settings.MEDRIGHTS_STORAGE_ROOT):
        shutil.rmtree(settings.MEDRIGHTS_STORAGE_ROOT, ignore_errors=True)


# ------------------------------------------------------------------
# Upload
# ------------------------------------------------------------------

class TestMediaUpload:
    def test_upload_media(self, auth_client):
        """POST multipart with a real small PNG image, verify 201."""
        img = _create_test_image()
        resp = auth_client.post(
            "/api/v1/media/upload/",
            {"file": img},
            format="multipart",
        )
        assert resp.status_code == 201
        data = resp.data
        assert "id" in data
        assert data["original_filename"] == "test.png"
        assert data["originality_status"] == "original"
        assert data["mime_type"] in ("image/png",)


# ------------------------------------------------------------------
# List
# ------------------------------------------------------------------

class TestMediaList:
    def test_list_media(self, auth_client):
        """GET returns paginated list."""
        # Upload one image first
        img = _create_test_image()
        auth_client.post("/api/v1/media/upload/", {"file": img}, format="multipart")

        resp = auth_client.get("/api/v1/media/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "results" in resp.data
        assert resp.data["count"] >= 1


# ------------------------------------------------------------------
# Detail
# ------------------------------------------------------------------

class TestMediaDetail:
    def test_media_detail(self, auth_client):
        """GET returns full detail."""
        img = _create_test_image()
        upload_resp = auth_client.post(
            "/api/v1/media/upload/", {"file": img}, format="multipart",
        )
        media_id = upload_resp.data["id"]

        resp = auth_client.get(f"/api/v1/media/{media_id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == media_id
        assert "pixel_hash" in resp.data


# ------------------------------------------------------------------
# Originality (duplicate detection)
# ------------------------------------------------------------------

class TestOriginalityDuplicate:
    def test_originality_duplicate(self, auth_client):
        """Upload same image twice; second should be 'reposted'."""
        img1 = _create_test_image(color="blue")
        resp1 = auth_client.post(
            "/api/v1/media/upload/", {"file": img1}, format="multipart",
        )
        assert resp1.status_code == 201
        assert resp1.data["originality_status"] == "original"

        img2 = _create_test_image(color="blue")
        resp2 = auth_client.post(
            "/api/v1/media/upload/", {"file": img2}, format="multipart",
        )
        assert resp2.status_code == 201
        assert resp2.data["originality_status"] == "reposted"


# ------------------------------------------------------------------
# Infringement - compliance only
# ------------------------------------------------------------------

class TestInfringementCreateComplianceOnly:
    def test_compliance_user_can_create(self, compliance_client):
        """Compliance user can create an infringement report."""
        resp = compliance_client.post(
            "/api/v1/media/infringement/",
            {"notes": "Potential infringement found on external site.", "reference": "https://example.com/infringing"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["status"] == "open"

    def test_frontdesk_gets_403(self, frontdesk_client):
        """Front desk user gets 403 when trying to create infringement."""
        resp = frontdesk_client.post(
            "/api/v1/media/infringement/",
            {"notes": "Trying to create.", "reference": "ref"},
            format="json",
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Infringement state transition
# ------------------------------------------------------------------

class TestInfringementStateTransition:
    def test_state_transition(self, compliance_client):
        """Create -> update to investigating -> resolve."""
        create_resp = compliance_client.post(
            "/api/v1/media/infringement/",
            {"notes": "Initial report", "reference": "https://example.com/issue"},
            format="json",
        )
        report_id = create_resp.data["id"]
        assert create_resp.data["status"] == "open"

        # Transition to investigating
        resp2 = compliance_client.patch(
            f"/api/v1/media/infringement/{report_id}/",
            {"status": "investigating", "notes": "Looking into it"},
            format="json",
        )
        assert resp2.status_code == 200
        assert resp2.data["status"] == "investigating"

        # Transition to resolved
        resp3 = compliance_client.patch(
            f"/api/v1/media/infringement/{report_id}/",
            {"status": "resolved", "notes": "Issue resolved"},
            format="json",
        )
        assert resp3.status_code == 200
        assert resp3.data["status"] == "resolved"


# ------------------------------------------------------------------
# Repost download blocked
# ------------------------------------------------------------------

class TestRepostDownloadBlocked:
    def test_repost_download_blocked(self, auth_client):
        """Upload image, set originality_status='reposted', download without citation returns 403."""
        img = _create_test_image(color="green")
        upload_resp = auth_client.post(
            "/api/v1/media/upload/", {"file": img}, format="multipart",
        )
        media_id = upload_resp.data["id"]

        # Manually set originality_status to reposted
        asset = MediaAsset.objects.get(pk=media_id)
        asset.originality_status = "reposted"
        asset.save(update_fields=["originality_status"])

        # Download should be blocked (no citation exists)
        resp = auth_client.get(f"/api/v1/media/{media_id}/download/")
        assert resp.status_code == 403
        assert resp.data["error"] == "repost_not_authorized"


# ------------------------------------------------------------------
# Watermark
# ------------------------------------------------------------------

class TestWatermark:
    def test_watermark(self, auth_client):
        """POST watermark config, verify watermark_burned is True."""
        img = _create_test_image(color="yellow", size=(100, 100))
        upload_resp = auth_client.post(
            "/api/v1/media/upload/", {"file": img}, format="multipart",
        )
        media_id = upload_resp.data["id"]

        resp = auth_client.post(
            f"/api/v1/media/{media_id}/watermark/",
            {
                "clinic_name": "Test Clinic",
                "date_stamp": True,
                "opacity": 0.5,
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["watermark_burned"] is True
