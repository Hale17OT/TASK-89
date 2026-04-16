"""Black-box tests: Orders, Payments, Refunds, Reconciliation."""
import json
import uuid

from .conftest import (
    WS, admin, frontdesk, clinician, anon,
    assert_denied, assert_role_denied, create_order, create_patient,
)


class TestOrderListCreate:
    def test_order_list(self):
        create_order()
        r = admin().get("/api/v1/financials/orders/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert "results" in body
        assert body["count"] >= 1

    def test_order_create(self):
        o = create_order()
        assert "id" in o
        assert "order_number" in o
        assert o["status"] in ("open", "pending")

    def test_order_create_anon_denied(self):
        p = create_patient()
        assert_denied(anon().post(
            "/api/v1/financials/orders/",
            json.dumps({
                "patient_id": p["id"],
                "line_items": [{"description": "X", "quantity": 1, "unit_price": "10.00"}],
            }),
            content_type="application/json",
            **WS,
        ))

    def test_order_create_clinician_denied(self):
        p = create_patient()
        r = clinician().post(
            "/api/v1/financials/orders/",
            json.dumps({
                "patient_id": p["id"],
                "line_items": [{"description": "X", "quantity": 1, "unit_price": "10.00"}],
            }),
            content_type="application/json",
            **WS,
        )
        assert_role_denied(r)


class TestOrderDetail:
    def test_order_detail(self):
        o = create_order()
        r = admin().get(f"/api/v1/financials/orders/{o['id']}/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == o["id"]
        assert "total_amount" in body

    def test_order_detail_not_found(self):
        r = admin().get(f"/api/v1/financials/orders/{uuid.uuid4()}/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"


class TestOrderPayment:
    def test_order_payment(self):
        o = create_order()
        r = admin().post(
            f"/api/v1/financials/orders/{o['id']}/payments/",
            json.dumps({
                "amount": 50.00,
                "method": "cash",
            }),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            **WS,
        )
        assert r.status_code == 201
        body = r.json()
        assert "id" in body

    def test_order_payment_anon_denied(self):
        o = create_order()
        assert_denied(anon().post(
            f"/api/v1/financials/orders/{o['id']}/payments/",
            json.dumps({"amount": 50.00, "method": "cash"}),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            **WS,
        ))


class TestReconciliationDetail:
    def test_reconciliation_detail_success(self, tmp_path):
        from apps.financials.models import DailyReconciliation
        csv_file = tmp_path / "recon.csv"
        csv_file.write_text("header\nrow")
        DailyReconciliation.objects.create(
            reconciliation_date="2025-02-15",
            total_orders=3,
            total_revenue="300.00",
            total_payments="300.00",
            total_refunds="0.00",
            discrepancy="0.00",
            csv_file_path=str(csv_file),
            generated_by="test",
        )
        r = admin().get("/api/v1/financials/reconciliation/2025-02-15/", **WS)
        assert r.status_code == 200
        body = r.json()
        assert body["reconciliation_date"] == "2025-02-15"
        assert body["total_orders"] == 3

    def test_reconciliation_detail_not_found(self):
        r = admin().get("/api/v1/financials/reconciliation/1999-01-01/", **WS)
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"
