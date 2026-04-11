"""Unit tests for pure-Python domain services (no DB required)."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from domain.exceptions import ConflictError, ValidationError
from domain.services.consent_service import (
    compute_consent_status,
    validate_consent_dates,
    validate_revocation,
)
from domain.services.financial_service import (
    compute_order_total,
    validate_payment_amount,
    validate_refund_amount,
)


# ------------------------------------------------------------------
# Consent status
# ------------------------------------------------------------------

class TestComputeConsentStatus:
    def test_compute_consent_status_active(self):
        status = compute_consent_status(
            is_revoked=False,
            expiration_date=date.today() + timedelta(days=30),
            effective_date=date.today() - timedelta(days=10),
        )
        assert status == "active"

    def test_compute_consent_status_expired(self):
        status = compute_consent_status(
            is_revoked=False,
            expiration_date=date.today() - timedelta(days=1),
            effective_date=date.today() - timedelta(days=60),
        )
        assert status == "expired"

    def test_compute_consent_status_revoked(self):
        status = compute_consent_status(
            is_revoked=True,
            expiration_date=date.today() + timedelta(days=30),
            effective_date=date.today() - timedelta(days=10),
        )
        assert status == "revoked"


# ------------------------------------------------------------------
# Consent date validation
# ------------------------------------------------------------------

class TestValidateConsentDates:
    def test_validate_consent_dates_valid(self):
        # Should not raise
        validate_consent_dates(
            effective_date=date.today(),
            expiration_date=date.today() + timedelta(days=30),
        )

    def test_validate_consent_dates_none_expiration(self):
        # None expiration (indefinite consent) should not raise
        validate_consent_dates(
            effective_date=date.today(),
            expiration_date=None,
        )

    def test_validate_consent_dates_invalid(self):
        with pytest.raises(ValidationError, match="after the effective date"):
            validate_consent_dates(
                effective_date=date.today(),
                expiration_date=date.today() - timedelta(days=1),
            )

    def test_validate_consent_dates_same_day(self):
        """Expiration on the same day as effective is invalid (must be after)."""
        with pytest.raises(ValidationError):
            validate_consent_dates(
                effective_date=date.today(),
                expiration_date=date.today(),
            )


# ------------------------------------------------------------------
# Revocation validation
# ------------------------------------------------------------------

class TestValidateRevocation:
    def test_revoke_already_revoked(self):
        with pytest.raises(ConflictError, match="already been revoked"):
            validate_revocation(
                is_revoked=True,
                physical_copy_on_file=False,
                acknowledged_warning=False,
            )

    def test_revoke_physical_copy_without_ack(self):
        with pytest.raises(ValidationError, match="physical_copy_warning"):
            validate_revocation(
                is_revoked=False,
                physical_copy_on_file=True,
                acknowledged_warning=False,
            )


# ------------------------------------------------------------------
# Financial: payment / refund validation
# ------------------------------------------------------------------

class TestValidatePaymentAmount:
    def test_validate_payment_exceeds_balance(self):
        order = SimpleNamespace(
            total_amount=Decimal("100.00"),
            amount_paid=Decimal("80.00"),
        )
        errors = validate_payment_amount(order, Decimal("30.00"))
        assert len(errors) == 1
        assert "exceeds remaining balance" in errors[0]

    def test_validate_payment_exact_balance(self):
        order = SimpleNamespace(
            total_amount=Decimal("100.00"),
            amount_paid=Decimal("80.00"),
        )
        errors = validate_payment_amount(order, Decimal("20.00"))
        assert errors == []


class TestValidateRefundAmount:
    def test_validate_refund_exceeds_paid(self):
        order = SimpleNamespace(amount_paid=Decimal("50.00"))
        errors = validate_refund_amount(order, Decimal("60.00"))
        assert len(errors) == 1
        assert "exceeds total paid" in errors[0]

    def test_validate_refund_within_paid(self):
        order = SimpleNamespace(amount_paid=Decimal("50.00"))
        errors = validate_refund_amount(order, Decimal("50.00"))
        assert errors == []


# ------------------------------------------------------------------
# Financial: order total computation
# ------------------------------------------------------------------

class TestComputeOrderTotal:
    def test_compute_order_total(self):
        items = [
            {"quantity": 2, "unit_price": "10.50"},
            {"quantity": 1, "unit_price": "25.00"},
        ]
        result = compute_order_total(items)
        assert result["subtotal"] == Decimal("46.00")
        assert result["tax_amount"] == Decimal("0.00")
        assert result["total_amount"] == Decimal("46.00")
