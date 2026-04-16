"""Black-box tests: Report Subscriptions, Outbox, Dashboard."""
import json
import uuid

from .conftest import (
    WS, admin, frontdesk, compliance, anon,
    assert_denied, assert_role_denied,
)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

class TestSubscriptionListCreate:
    def test_subscription_list(self):
        r = admin().get("/api/v1/reports/subscriptions/", **WS)
        assert r.status_code == 200
        assert "results" in r.json()

    def test_subscription_create(self):
        r = admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Daily Recon BB",
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
        body = r.json()
        assert body["name"] == "Daily Recon BB"
        assert "id" in body

    def test_subscription_list_frontdesk_denied(self):
        assert_role_denied(frontdesk().get("/api/v1/reports/subscriptions/", **WS))


class TestSubscriptionDetail:
    def _make_sub(self):
        r = admin().post(
            "/api/v1/reports/subscriptions/",
            json.dumps({
                "name": "Sub Detail BB",
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
        r = admin().get(f"/api/v1/reports/subscriptions/{sub['id']}/", **WS)
        assert r.status_code == 200
        assert r.json()["id"] == sub["id"]

    def test_subscription_patch(self):
        sub = self._make_sub()
        r = admin().patch(
            f"/api/v1/reports/subscriptions/{sub['id']}/",
            json.dumps({"name": "Renamed BB"}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed BB"

    def test_subscription_delete(self):
        sub = self._make_sub()
        r = admin().delete(f"/api/v1/reports/subscriptions/{sub['id']}/", **WS)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------

def _make_outbox_item(status="delivered", file_path=""):
    from apps.reports.models import OutboxItem
    return OutboxItem.objects.create(
        report_name="BB Test Report",
        file_format="pdf",
        status=status,
        file_path=file_path,
        delivery_target="shared_folder",
    )


class TestOutboxDetail:
    def test_outbox_detail_success(self):
        item = _make_outbox_item()
        r = admin().get(f"/api/v1/reports/outbox/{item.pk}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["report_name"] == "BB Test Report"
        assert "status" in body
        assert "file_format" in body

    def test_outbox_detail_not_found(self):
        r = admin().get(f"/api/v1/reports/outbox/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"


class TestOutboxDownload:
    def test_outbox_download_success(self, tmp_path):
        f = tmp_path / "report_bb.pdf"
        f.write_text("fake pdf")
        item = _make_outbox_item(file_path=str(f))
        r = admin().get(f"/api/v1/reports/outbox/{item.pk}/download/", **WS)
        assert r.status_code == 200

    def test_outbox_download_not_found(self):
        r = admin().get(f"/api/v1/reports/outbox/{uuid.uuid4()}/download/", **WS)
        assert r.status_code == 404


class TestOutboxRetry:
    def test_outbox_retry_success(self):
        item = _make_outbox_item(status="failed")
        r = admin().post(
            f"/api/v1/reports/outbox/{item.pk}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "message" in body

    def test_outbox_retry_not_found(self):
        r = admin().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"

    def test_outbox_retry_frontdesk_denied(self):
        assert_role_denied(frontdesk().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/retry/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        ))


class TestOutboxAcknowledge:
    def test_outbox_acknowledge_success(self):
        item = _make_outbox_item(status="stalled")
        r = admin().post(
            f"/api/v1/reports/outbox/{item.pk}/acknowledge/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 200

    def test_outbox_acknowledge_not_found(self):
        r = admin().post(
            f"/api/v1/reports/outbox/{uuid.uuid4()}/acknowledge/",
            json.dumps({}),
            content_type="application/json",
            **WS,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestReportDashboard:
    def test_dashboard(self):
        r = admin().get("/api/v1/reports/dashboard/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "queued" in body

    def test_dashboard_compliance(self):
        r = compliance().get("/api/v1/reports/dashboard/", **WS)
        assert r.status_code == 200

    def test_dashboard_frontdesk_denied(self):
        assert_role_denied(frontdesk().get("/api/v1/reports/dashboard/", **WS))
