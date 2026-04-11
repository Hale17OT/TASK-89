"""Integration tests for financial task audit-chain writes.

Verifies that ``auto_close_unpaid_orders`` and
``generate_daily_reconciliation`` create tamper-evident AuditEntry
records when they modify financial state.
"""
import os
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEntry
from apps.financials.models import DailyReconciliation, Order, Payment

pytestmark = pytest.mark.django_db(transaction=True)


# ── Helpers ─────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="fin_task_admin", password="Pass123!!", role="admin",
    )


@pytest.fixture
def patient_id(admin_user):
    """Create a patient via the API and return the ID."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=admin_user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "ws-fin-task"
    resp = client.post("/api/v1/patients/create/", {
        "mrn": "FIN-TASK-001",
        "first_name": "Fin",
        "last_name": "Task",
        "date_of_birth": "1990-01-01",
        "gender": "M",
    }, format="json")
    assert resp.status_code == 201
    return resp.data["id"]


@pytest.fixture(autouse=True)
def _ensure_storage():
    storage = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    os.makedirs(os.path.join(storage, "reconciliation"), exist_ok=True)
    yield


# ── auto_close_unpaid_orders ────────────────────────────────────────────

class TestAutoCloseAuditEntry:
    def test_auto_close_creates_audit_entry(self, admin_user, patient_id):
        """auto_close_unpaid_orders must write a financial_auto_close audit entry."""
        order = Order.objects.create(
            order_number="ORD-AUDIT-001",
            patient_id=patient_id,
            status="open",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            created_by=admin_user,
            auto_close_at=timezone.now() - timedelta(minutes=5),
        )

        before_count = AuditEntry.objects.count()

        from apps.financials.tasks import auto_close_unpaid_orders
        result = auto_close_unpaid_orders()

        assert result["closed_count"] == 1

        order.refresh_from_db()
        assert order.status == "closed_unpaid"

        # Verify audit entry was created
        new_entries = AuditEntry.objects.filter(id__gt=before_count)
        audit = new_entries.filter(event_type="financial_auto_close").first()
        assert audit is not None, "No financial_auto_close audit entry found"
        assert audit.target_model == "Order"
        assert audit.target_id == str(order.pk)
        assert audit.target_repr == order.order_number
        assert audit.username_snapshot == "celery_beat"
        assert audit.field_changes["status"]["old"] == "open"
        assert audit.field_changes["status"]["new"] == "closed_unpaid"

    def test_auto_close_no_eligible_orders_no_audit(self, admin_user, patient_id):
        """No audit entries when there's nothing to close."""
        Order.objects.create(
            order_number="ORD-AUDIT-002",
            patient_id=patient_id,
            status="open",
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            created_by=admin_user,
            auto_close_at=timezone.now() + timedelta(hours=1),  # future
        )

        before_count = AuditEntry.objects.count()

        from apps.financials.tasks import auto_close_unpaid_orders
        result = auto_close_unpaid_orders()

        assert result["closed_count"] == 0
        assert AuditEntry.objects.count() == before_count

    def test_auto_close_multiple_orders_multiple_audits(self, admin_user, patient_id):
        """Each closed order gets its own audit entry."""
        past = timezone.now() - timedelta(minutes=10)
        for i in range(3):
            Order.objects.create(
                order_number=f"ORD-MULTI-{i:03d}",
                patient_id=patient_id,
                status="open",
                subtotal=Decimal("10.00"),
                total_amount=Decimal("10.00"),
                created_by=admin_user,
                auto_close_at=past,
            )

        before_count = AuditEntry.objects.count()

        from apps.financials.tasks import auto_close_unpaid_orders
        result = auto_close_unpaid_orders()

        assert result["closed_count"] == 3

        new_audits = AuditEntry.objects.filter(
            event_type="financial_auto_close",
            id__gt=before_count,
        ).count()
        assert new_audits == 3


# ── generate_daily_reconciliation ───────────────────────────────────────

class TestReconciliationAuditEntry:
    def test_reconciliation_creates_audit_entry(self, admin_user, patient_id):
        """generate_daily_reconciliation must write a reconciliation audit entry."""
        target = date.today() - timedelta(days=2)

        before_count = AuditEntry.objects.count()

        from apps.financials.tasks import generate_daily_reconciliation
        result = generate_daily_reconciliation(str(target))

        assert result["status"] == "generated"

        # Verify audit entry
        audit = AuditEntry.objects.filter(
            event_type="financial_reconciliation_generated",
            id__gt=before_count,
        ).first()
        assert audit is not None, "No reconciliation audit entry found"
        assert audit.target_model == "DailyReconciliation"
        assert audit.username_snapshot == "celery_beat"
        assert audit.extra_data["reconciliation_date"] == str(target)
        assert "total_orders" in audit.extra_data
        assert "discrepancy" in audit.extra_data

    def test_reconciliation_idempotent_no_duplicate_audit(self, admin_user, patient_id):
        """Running reconciliation twice for the same date doesn't create a second entry."""
        target = date.today() - timedelta(days=3)

        from apps.financials.tasks import generate_daily_reconciliation
        result1 = generate_daily_reconciliation(str(target))
        assert result1["status"] == "generated"

        before_count = AuditEntry.objects.count()

        result2 = generate_daily_reconciliation(str(target))
        assert result2["status"] == "already_exists"

        # No new audit entries
        assert AuditEntry.objects.count() == before_count
