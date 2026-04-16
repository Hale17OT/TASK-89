"""Black-box tests: Media upload/list/detail/download/watermark, Infringements."""
import json

from .conftest import (
    WS, admin, frontdesk, clinician, compliance, anon,
    assert_denied, assert_role_denied, upload_media, create_patient, test_image,
)


class TestMediaUpload:
    def test_upload_success(self):
        m = upload_media()
        assert "id" in m
        assert m["originality_status"] == "original"
        assert "pixel_hash" in m

    def test_upload_anon_denied(self):
        assert_denied(anon().post("/api/v1/media/upload/", {"file": test_image()}, **WS))

    def test_upload_compliance_denied(self):
        r = compliance().post("/api/v1/media/upload/", {"file": test_image()}, **WS)
        assert_role_denied(r)


class TestMediaList:
    def test_media_list(self):
        upload_media()
        r = admin().get("/api/v1/media/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "results" in body
        assert body["count"] >= 1

    def test_media_list_anon_denied(self):
        assert_denied(anon().get("/api/v1/media/", **WS))


class TestMediaDetail:
    def test_media_detail(self):
        m = upload_media()
        r = admin().get(f"/api/v1/media/{m['id']}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == m["id"]
        assert "mime_type" in body
        assert "pixel_hash" in body

    def test_media_detail_not_found(self):
        import uuid
        r = admin().get(f"/api/v1/media/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"


class TestMediaAttachPatient:
    def test_attach_patient(self):
        m = upload_media()
        p = create_patient()
        r = admin().post(
            f"/api/v1/media/{m['id']}/attach-patient/",
            json.dumps({"patient_id": p["id"]}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["patient_id"] == p["id"]

    def test_attach_patient_anon_denied(self):
        m = upload_media()
        p = create_patient()
        assert_denied(anon().post(
            f"/api/v1/media/{m['id']}/attach-patient/",
            json.dumps({"patient_id": p["id"]}),
            content_type="application/json",
            **WS,
        ))


class TestInfringementCreate:
    def test_infringement_list(self):
        r = compliance().get("/api/v1/media/infringement/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_infringement_create(self):
        m = upload_media()
        r = compliance().post(
            "/api/v1/media/infringement/",
            {
                "notes": "Possible copyright violation found in this media asset.",
                "media_asset_id": m["id"],
                "reference": "https://example.com/original",
            },
            **WS,
        )
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["status"] == "open"

    def test_infringement_list_frontdesk_denied(self):
        assert_role_denied(frontdesk().get("/api/v1/media/infringement/", **WS))
