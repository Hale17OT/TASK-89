"""Financial serializers: Order, Payment, Refund, Reconciliation."""
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from domain.services.financial_service import (
    compute_order_total,
    generate_order_number,
    validate_payment_amount,
    validate_refund_amount,
)

from .models import (
    CompensatingEntry,
    DailyReconciliation,
    IdempotencyKey,
    Order,
    OrderLineItem,
    Payment,
    Refund,
)

logger = logging.getLogger("medrights.financials")


# ── Line-item helpers ─────────────────────────────────────────────────

class LineItemInputSerializer(serializers.Serializer):
    """Input format for a single order line item."""

    description = serializers.CharField(max_length=500)
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))


class LineItemOutputSerializer(serializers.Serializer):
    """Read-only representation of an order line item."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "description": instance.description,
            "quantity": instance.quantity,
            "unit_price": str(instance.unit_price),
            "line_total": str(instance.line_total),
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }


# ── OrderCreateSerializer ────────────────────────────────────────────

class OrderCreateSerializer(serializers.Serializer):
    """Create a new order with line items."""

    patient_id = serializers.UUIDField()
    line_items = LineItemInputSerializer(many=True, min_length=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_patient_id(self, value):
        from apps.mpi.models import Patient

        try:
            Patient.objects.get(pk=value)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found.")
        return value

    def validate_line_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value

    def create(self, validated_data):
        from apps.mpi.models import Patient

        user = self.context["request"].user
        patient = Patient.objects.get(pk=validated_data["patient_id"])
        line_items_data = validated_data["line_items"]
        notes = validated_data.get("notes", "")

        totals = compute_order_total(line_items_data)

        with transaction.atomic():
            order_number = generate_order_number()
            now = timezone.now()

            order = Order.objects.create(
                order_number=order_number,
                patient=patient,
                status="open",
                subtotal=totals["subtotal"],
                tax_amount=totals["tax_amount"],
                total_amount=totals["total_amount"],
                amount_paid=Decimal("0.00"),
                notes=notes,
                created_by=user,
                auto_close_at=now + timedelta(minutes=30),
            )

            for item_data in line_items_data:
                qty = int(item_data["quantity"])
                price = Decimal(str(item_data["unit_price"]))
                line_total = (price * qty).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                OrderLineItem.objects.create(
                    order=order,
                    description=item_data["description"],
                    quantity=qty,
                    unit_price=price,
                    line_total=line_total,
                )

        logger.info(
            "Order created: order_number=%s patient=%s total=%s",
            order.order_number,
            patient.id,
            order.total_amount,
        )
        return order

    def to_representation(self, instance):
        return OrderDetailSerializer(instance).data


# ── OrderListSerializer ──────────────────────────────────────────────

class OrderListSerializer(serializers.Serializer):
    """Read-only order summary including time remaining for open orders."""

    def to_representation(self, instance):
        now = timezone.now()
        time_remaining = None

        if instance.status == "open" and instance.auto_close_at:
            delta = instance.auto_close_at - now
            remaining_seconds = max(int(delta.total_seconds()), 0)
            time_remaining = remaining_seconds

        return {
            "id": str(instance.id),
            "order_number": instance.order_number,
            "patient_id": str(instance.patient_id),
            "status": instance.status,
            "subtotal": str(instance.subtotal),
            "tax_amount": str(instance.tax_amount),
            "total_amount": str(instance.total_amount),
            "amount_paid": str(instance.amount_paid),
            "notes": instance.notes,
            "created_by": str(instance.created_by_id),
            "auto_close_at": instance.auto_close_at.isoformat() if instance.auto_close_at else None,
            "time_remaining_seconds": time_remaining,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }


# ── OrderDetailSerializer ────────────────────────────────────────────

class PaymentOutputSerializer(serializers.Serializer):
    """Read-only representation of a payment."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "amount": str(instance.amount),
            "payment_method": instance.payment_method,
            "check_number": instance.check_number,
            "reference_note": instance.reference_note,
            "is_compensating": instance.is_compensating,
            "compensates_id": str(instance.compensates_id) if instance.compensates_id else None,
            "posted_by": str(instance.posted_by_id),
            "posted_at": instance.posted_at.isoformat() if instance.posted_at else None,
        }


class CompensatingEntryOutputSerializer(serializers.Serializer):
    """Read-only representation of a compensating entry."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "parent_entry_id": str(instance.parent_entry_id) if instance.parent_entry_id else None,
            "parent_entry_type": instance.parent_entry_type,
            "entry_type": instance.entry_type,
            "amount": str(instance.amount),
            "reason": instance.reason,
            "created_by": str(instance.created_by_id),
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }


class RefundOutputSerializer(serializers.Serializer):
    """Read-only representation of a refund."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "original_payment_id": str(instance.original_payment_id),
            "compensating_entry_id": str(instance.compensating_entry_id) if instance.compensating_entry_id else None,
            "amount": str(instance.amount),
            "reason": instance.reason,
            "status": instance.status,
            "requested_by": str(instance.requested_by_id),
            "approved_by": str(instance.approved_by_id) if instance.approved_by_id else None,
            "approved_at": instance.approved_at.isoformat() if instance.approved_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }


class OrderDetailSerializer(serializers.Serializer):
    """Full order detail with line items and transaction history."""

    def to_representation(self, instance):
        now = timezone.now()
        time_remaining = None

        if instance.status == "open" and instance.auto_close_at:
            delta = instance.auto_close_at - now
            remaining_seconds = max(int(delta.total_seconds()), 0)
            time_remaining = remaining_seconds

        line_items = instance.line_items.all()
        payments = instance.payments.all()
        compensating_entries = instance.compensating_entries.all()
        refunds = instance.refunds.all()

        return {
            "id": str(instance.id),
            "order_number": instance.order_number,
            "patient_id": str(instance.patient_id),
            "status": instance.status,
            "subtotal": str(instance.subtotal),
            "tax_amount": str(instance.tax_amount),
            "total_amount": str(instance.total_amount),
            "amount_paid": str(instance.amount_paid),
            "notes": instance.notes,
            "created_by": str(instance.created_by_id),
            "auto_close_at": instance.auto_close_at.isoformat() if instance.auto_close_at else None,
            "time_remaining_seconds": time_remaining,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
            "line_items": LineItemOutputSerializer(line_items, many=True).data,
            "payments": PaymentOutputSerializer(payments, many=True).data,
            "compensating_entries": CompensatingEntryOutputSerializer(
                compensating_entries, many=True
            ).data,
            "refunds": RefundOutputSerializer(refunds, many=True).data,
        }


# ── PaymentSerializer ────────────────────────────────────────────────

class PaymentSerializer(serializers.Serializer):
    """Record a payment against an order. Requires Idempotency-Key header."""

    method = serializers.ChoiceField(choices=["cash", "check"])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    check_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")

    def validate(self, data):
        order = self.context["order"]
        request = self.context["request"]

        # Require idempotency key
        idempotency_key = request.META.get("HTTP_IDEMPOTENCY_KEY", "")
        if not idempotency_key:
            raise serializers.ValidationError(
                {"non_field_errors": ["Idempotency-Key header is required."]}
            )

        # Validate order status
        if order.status not in ("open", "partial"):
            raise serializers.ValidationError(
                {"non_field_errors": [f"Cannot accept payment for order with status '{order.status}'."]}
            )

        # Validate payment amount
        errors = validate_payment_amount(order, data["amount"])
        if errors:
            raise serializers.ValidationError({"amount": errors})

        # Check for check number when method is check
        if data["method"] == "check" and not data.get("check_number", "").strip():
            raise serializers.ValidationError(
                {"check_number": "Check number is required for check payments."}
            )

        return data

    def create(self, validated_data):
        order = self.context["order"]
        user = self.context["request"].user
        request = self.context["request"]
        idempotency_key = request.META.get("HTTP_IDEMPOTENCY_KEY", "")

        with transaction.atomic():
            # Check idempotency
            existing = IdempotencyKey.objects.filter(
                key=idempotency_key,
                expires_at__gt=timezone.now(),
            ).first()

            if existing:
                # Return cached response data
                self._idempotent_response = existing.response_data
                return None

            payment = Payment.objects.create(
                order=order,
                amount=validated_data["amount"],
                payment_method=validated_data["method"],
                check_number=validated_data.get("check_number", ""),
                posted_by=user,
            )

            # Update order totals
            order.amount_paid += validated_data["amount"]
            if order.amount_paid >= order.total_amount:
                order.status = "paid"
            else:
                order.status = "partial"
            order.save()

            # Build response data
            response_data = PaymentOutputSerializer(payment).data

            # Store idempotency key
            IdempotencyKey.objects.create(
                key=idempotency_key,
                response_data=response_data,
                expires_at=timezone.now() + timedelta(hours=24),
            )

            self._idempotent_response = None

            logger.info(
                "Payment recorded: payment_id=%s order=%s amount=%s method=%s",
                payment.id,
                order.order_number,
                payment.amount,
                payment.payment_method,
            )
            return payment

    def to_representation(self, instance):
        # If we hit an idempotent duplicate, return the cached data
        if hasattr(self, "_idempotent_response") and self._idempotent_response is not None:
            return self._idempotent_response
        if instance is None:
            return self._idempotent_response
        return PaymentOutputSerializer(instance).data


# ── RefundCreateSerializer ───────────────────────────────────────────

class RefundCreateSerializer(serializers.Serializer):
    """Initiate a refund against an order."""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    reason = serializers.CharField(min_length=1)
    original_payment_id = serializers.UUIDField()

    def validate(self, data):
        order = self.context["order"]

        # Validate order has payments
        if order.amount_paid <= Decimal("0.00"):
            raise serializers.ValidationError(
                {"non_field_errors": ["No payments have been made on this order."]}
            )

        # Validate refund amount
        errors = validate_refund_amount(order, data["amount"])
        if errors:
            raise serializers.ValidationError({"amount": errors})

        # Validate original payment exists and belongs to this order
        try:
            payment = Payment.objects.get(
                pk=data["original_payment_id"],
                order=order,
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                {"original_payment_id": "Payment not found for this order."}
            )

        data["_payment"] = payment
        return data

    def create(self, validated_data):
        order = self.context["order"]
        user = self.context["request"].user
        payment = validated_data["_payment"]

        refund = Refund.objects.create(
            order=order,
            original_payment=payment,
            amount=validated_data["amount"],
            reason=validated_data["reason"],
            status="pending",
            requested_by=user,
        )

        logger.info(
            "Refund requested: refund_id=%s order=%s amount=%s",
            refund.id,
            order.order_number,
            refund.amount,
        )
        return refund

    def to_representation(self, instance):
        return RefundOutputSerializer(instance).data


# ── RefundApproveSerializer ──────────────────────────────────────────

class RefundApproveSerializer(serializers.Serializer):
    """Admin approval of a pending refund."""

    def validate(self, data):
        refund = self.context["refund"]
        if refund.status != "pending":
            raise serializers.ValidationError(
                {"non_field_errors": [f"Cannot approve refund with status '{refund.status}'."]}
            )
        return data

    def save(self):
        refund = self.context["refund"]
        user = self.context["request"].user

        refund.status = "approved"
        refund.approved_by = user
        refund.approved_at = timezone.now()
        refund.save()

        logger.info(
            "Refund approved: refund_id=%s order=%s by=%s",
            refund.id,
            refund.order.order_number,
            user.id,
        )
        return refund


# ── RefundProcessSerializer ──────────────────────────────────────────

class RefundProcessSerializer(serializers.Serializer):
    """Process an approved refund -- creates a compensating entry."""

    def validate(self, data):
        refund = self.context["refund"]
        if refund.status != "approved":
            raise serializers.ValidationError(
                {"non_field_errors": [f"Cannot process refund with status '{refund.status}'."]}
            )
        return data

    def save(self):
        refund = self.context["refund"]
        user = self.context["request"].user

        with transaction.atomic():
            # Create compensating entry (negative amount for reversal)
            comp_entry = CompensatingEntry.objects.create(
                parent_entry_id=refund.original_payment_id,
                parent_entry_type="payment",
                entry_type="reversal",
                order=refund.order,
                amount=-refund.amount,
                reason=f"Refund: {refund.reason}",
                created_by=user,
            )

            # Update refund
            refund.compensating_entry = comp_entry
            refund.status = "completed"
            refund.completed_at = timezone.now()
            refund.save()

            # Update order
            order = refund.order
            order.amount_paid -= refund.amount
            if order.amount_paid <= Decimal("0.00"):
                order.amount_paid = Decimal("0.00")
                order.status = "refunded"
            elif order.amount_paid < order.total_amount:
                order.status = "partial"
            order.save()

        logger.info(
            "Refund processed: refund_id=%s order=%s comp_entry=%s",
            refund.id,
            order.order_number,
            comp_entry.id,
        )
        return refund


# ── ReconciliationSerializer ─────────────────────────────────────────

class ReconciliationSerializer(serializers.Serializer):
    """Read-only reconciliation summary."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "reconciliation_date": str(instance.reconciliation_date),
            "total_orders": instance.total_orders,
            "total_revenue": str(instance.total_revenue),
            "total_payments": str(instance.total_payments),
            "total_refunds": str(instance.total_refunds),
            "discrepancy": str(instance.discrepancy),
            "csv_file_url": f"/api/v1/financials/reconciliation/{instance.reconciliation_date}/download/?format=csv",
            "pdf_file_url": (
                f"/api/v1/financials/reconciliation/{instance.reconciliation_date}/download/?format=pdf"
                if instance.pdf_file_path else None
            ),
            "generated_at": instance.generated_at.isoformat() if instance.generated_at else None,
            "generated_by": instance.generated_by,
            "is_deferred": instance.is_deferred,
        }
