"""Financial models: Order, Payment, Refund, CompensatingEntry, etc.

All financial models use the NoDeleteMixin to prevent hard deletes.
Financial records are immutable -- corrections are made via compensating entries.
"""
import uuid

from django.conf import settings
from django.db import models


# ── No-Delete Infrastructure ──────────────────────────────────────────

class NoDeleteMixin(models.Model):
    """Abstract mixin that prevents deletion of financial records."""

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "Financial records cannot be deleted. Use compensating entries."
        )


class NoDeleteQuerySet(models.QuerySet):
    """QuerySet that prevents bulk deletion of financial records."""

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "Financial records cannot be deleted. Use compensating entries."
        )


class NoDeleteManager(models.Manager):
    """Manager that returns NoDeleteQuerySet instances."""

    def get_queryset(self):
        return NoDeleteQuerySet(self.model, using=self._db)


# ── Order ─────────────────────────────────────────────────────────────

class Order(NoDeleteMixin):
    """A patient financial order (bill)."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("closed_unpaid", "Closed Unpaid"),
        ("voided", "Voided"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    patient = models.ForeignKey(
        "mpi.Patient",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_orders",
    )
    auto_close_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NoDeleteManager()

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} ({self.status})"


# ── OrderLineItem ─────────────────────────────────────────────────────

class OrderLineItem(NoDeleteMixin):
    """A single line item on an order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="line_items",
    )
    description = models.CharField(max_length=500)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NoDeleteManager()

    class Meta:
        db_table = "order_line_items"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.description} x{self.quantity} = {self.line_total}"


# ── Payment ───────────────────────────────────────────────────────────

class Payment(NoDeleteMixin):
    """A payment recorded against an order."""

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("check", "Check"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    check_number = models.CharField(max_length=50, blank=True, default="")
    reference_note = models.TextField(blank=True, default="")
    is_compensating = models.BooleanField(default=False)
    compensates = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="compensated_by",
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posted_payments",
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    objects = NoDeleteManager()

    class Meta:
        db_table = "payments"
        ordering = ["-posted_at"]

    def __str__(self):
        return f"Payment {self.id} -- {self.amount} ({self.payment_method})"


# ── CompensatingEntry ─────────────────────────────────────────────────

class CompensatingEntry(NoDeleteMixin):
    """
    A compensating (correction) entry for reversals or adjustments.
    Amount is negative for reversals.
    """

    PARENT_ENTRY_TYPE_CHOICES = [
        ("payment", "Payment"),
        ("compensating_entry", "Compensating Entry"),
    ]

    ENTRY_TYPE_CHOICES = [
        ("reversal", "Reversal"),
        ("adjustment", "Adjustment"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_entry_id = models.UUIDField(null=True, blank=True)
    parent_entry_type = models.CharField(
        max_length=20,
        choices=PARENT_ENTRY_TYPE_CHOICES,
        default="payment",
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="compensating_entries",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="compensating_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NoDeleteManager()

    class Meta:
        db_table = "compensating_entries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CompensatingEntry {self.id} -- {self.entry_type} {self.amount}"


# ── Refund ────────────────────────────────────────────────────────────

class Refund(NoDeleteMixin):
    """A refund request against an order."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("denied", "Denied"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    original_payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    compensating_entry = models.ForeignKey(
        CompensatingEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_refunds",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_refunds",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NoDeleteManager()

    class Meta:
        db_table = "refunds"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.id} -- {self.amount} ({self.status})"


# ── DailyReconciliation ──────────────────────────────────────────────

class DailyReconciliation(models.Model):
    """End-of-day reconciliation snapshot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reconciliation_date = models.DateField(unique=True, db_index=True)
    total_orders = models.IntegerField()
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2)
    total_refunds = models.DecimalField(max_digits=12, decimal_places=2)
    discrepancy = models.DecimalField(max_digits=12, decimal_places=2)
    csv_file_path = models.CharField(max_length=500)
    pdf_file_path = models.CharField(max_length=500, blank=True, default="")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=50)
    is_deferred = models.BooleanField(default=False)

    class Meta:
        db_table = "daily_reconciliation"
        ordering = ["-reconciliation_date"]

    def __str__(self):
        return f"Reconciliation {self.reconciliation_date}"


# ── IdempotencyKey ────────────────────────────────────────────────────

class IdempotencyKey(models.Model):
    """Idempotency key for duplicate payment protection."""

    key = models.CharField(max_length=64, primary_key=True)
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "idempotency_keys"

    def __str__(self):
        return f"IdempotencyKey {self.key}"
