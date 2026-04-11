"""Integration tests for the Financials API endpoints."""
import uuid
from decimal import Decimal

import pytest

from apps.financials.models import Order, Payment


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _create_order(client, patient_id, items=None, notes=""):
    """Helper to create an order via the API."""
    if items is None:
        items = [{"description": "Consultation", "quantity": 1, "unit_price": "100.00"}]
    return client.post(
        "/api/v1/financials/orders/",
        {"patient_id": str(patient_id), "line_items": items, "notes": notes},
        format="json",
    )


def _record_payment(client, order_id, amount="100.00", method="cash",
                     idempotency_key=None):
    """Helper to record a payment."""
    key = idempotency_key or str(uuid.uuid4())
    payload = {"method": method, "amount": amount}
    return client.post(
        f"/api/v1/financials/orders/{order_id}/payments/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )


# ------------------------------------------------------------------
# Orders
# ------------------------------------------------------------------

class TestOrderCreate:
    def test_create_order(self, auth_client, sample_patient):
        resp = _create_order(auth_client, sample_patient["id"])
        assert resp.status_code == 201
        data = resp.data
        assert data["order_number"].startswith("ORD-")
        assert data["status"] == "open"
        assert data["total_amount"] == "100.00"


# ------------------------------------------------------------------
# Payments
# ------------------------------------------------------------------

class TestPayments:
    def test_record_payment_cash(self, auth_client, sample_patient):
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]

        pay_resp = _record_payment(auth_client, order_id)
        assert pay_resp.status_code == 201

        # Verify order status is now 'paid'
        detail = auth_client.get(f"/api/v1/financials/orders/{order_id}/")
        assert detail.data["status"] == "paid"

    def test_record_payment_exceeds_balance(self, auth_client, sample_patient):
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]

        resp = _record_payment(auth_client, order_id, amount="200.00")
        assert resp.status_code == 400


# ------------------------------------------------------------------
# Refunds
# ------------------------------------------------------------------

class TestRefunds:
    def _paid_order(self, auth_client, sample_patient):
        """Create and fully pay an order, returning (order_id, payment data)."""
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]
        pay_resp = _record_payment(auth_client, order_id)
        return order_id, pay_resp.data

    def test_create_refund(self, auth_client, sample_patient):
        order_id, payment = self._paid_order(auth_client, sample_patient)
        resp = auth_client.post(
            f"/api/v1/financials/orders/{order_id}/refunds/",
            {
                "amount": "50.00",
                "reason": "Patient overpaid",
                "original_payment_id": payment["id"],
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["status"] == "pending"
        assert resp.data["amount"] == "50.00"

    def test_approve_refund(self, auth_client, sample_patient):
        order_id, payment = self._paid_order(auth_client, sample_patient)
        # Create refund
        refund_resp = auth_client.post(
            f"/api/v1/financials/orders/{order_id}/refunds/",
            {
                "amount": "100.00",
                "reason": "Full refund",
                "original_payment_id": payment["id"],
            },
            format="json",
        )
        refund_id = refund_resp.data["id"]

        # Approve (admin)
        approve_resp = auth_client.post(
            f"/api/v1/financials/refunds/{refund_id}/approve/",
            format="json",
        )
        assert approve_resp.status_code == 200
        assert approve_resp.data["status"] == "approved"


# ------------------------------------------------------------------
# NoDelete mixin
# ------------------------------------------------------------------

class TestNoDelete:
    def test_no_delete_order(self, auth_client, sample_patient):
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]

        with pytest.raises(PermissionError, match="cannot be deleted"):
            Order.objects.filter(pk=order_id).delete()

    def test_no_delete_payment(self, auth_client, sample_patient):
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]
        _record_payment(auth_client, order_id)

        with pytest.raises(PermissionError, match="cannot be deleted"):
            Payment.objects.filter(order_id=order_id).delete()


# ------------------------------------------------------------------
# Void
# ------------------------------------------------------------------

class TestVoidOrder:
    def test_void_order(self, auth_client, sample_patient):
        """Admin can void an unpaid order."""
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]

        void_resp = auth_client.post(
            f"/api/v1/financials/orders/{order_id}/void/",
            format="json",
        )
        assert void_resp.status_code == 200
        assert void_resp.data["status"] == "voided"

    def test_void_order_non_admin(self, frontdesk_client, auth_client, sample_patient):
        """Non-admin users cannot void orders."""
        order_resp = _create_order(auth_client, sample_patient["id"])
        order_id = order_resp.data["id"]

        void_resp = frontdesk_client.post(
            f"/api/v1/financials/orders/{order_id}/void/",
            format="json",
        )
        assert void_resp.status_code == 403
