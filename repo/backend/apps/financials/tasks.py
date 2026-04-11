"""Celery tasks for the financials app."""
import csv
import logging
import os
from datetime import date, timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger("medrights.financials")


@shared_task(name="apps.financials.tasks.auto_close_unpaid_orders")
def auto_close_unpaid_orders():
    """
    Close orders that have been open past their auto_close_at deadline.

    Runs every 60 seconds via Celery Beat. Idempotent -- only touches
    orders that are still 'open' and have passed their deadline.
    """
    from apps.financials.models import Order

    now = timezone.now()

    # Only select orders that are open and past their auto-close deadline
    expired_orders = Order.objects.filter(
        status="open",
        auto_close_at__isnull=False,
        auto_close_at__lte=now,
    )

    from apps.audit.service import create_audit_entry

    closed_count = 0
    for order in expired_orders.iterator():
        old_status = order.status
        order.status = "closed_unpaid"
        order.save(update_fields=["status", "updated_at"])
        closed_count += 1
        logger.info(
            "Auto-closed unpaid order: order_number=%s auto_close_at=%s",
            order.order_number,
            order.auto_close_at,
        )
        try:
            create_audit_entry(
                event_type="financial_auto_close",
                user=None,
                username_snapshot="celery_beat",
                client_ip="",
                workstation_id="",
                target_model="Order",
                target_id=str(order.pk),
                target_repr=order.order_number,
                field_changes={
                    "status": {"old": old_status, "new": "closed_unpaid"},
                },
                extra_data={
                    "auto_close_at": str(order.auto_close_at),
                    "trigger": "auto_close_unpaid_orders",
                },
            )
        except Exception:
            logger.exception(
                "Failed to write audit entry for auto-closed order %s",
                order.order_number,
            )

    if closed_count:
        logger.info("Auto-close task completed: %d order(s) closed.", closed_count)

    return {"closed_count": closed_count}


@shared_task(name="apps.financials.tasks.generate_daily_reconciliation")
def generate_daily_reconciliation(target_date=None):
    """
    Generate an end-of-day reconciliation report for a given date.

    If target_date is None, uses yesterday. Idempotent -- will not
    regenerate if a record already exists for that date.

    Args:
        target_date: ISO-format date string (YYYY-MM-DD) or None.
    """
    from apps.financials.models import (
        DailyReconciliation,
        Order,
        Payment,
        Refund,
    )

    if target_date:
        if isinstance(target_date, str):
            target = date.fromisoformat(target_date)
        else:
            target = target_date
    else:
        target = date.today() - timedelta(days=1)

    # Idempotency check
    if DailyReconciliation.objects.filter(reconciliation_date=target).exists():
        logger.info(
            "Reconciliation already exists for %s, skipping.", target
        )
        return {"status": "already_exists", "date": str(target)}

    # Aggregate data for the target date
    orders_qs = Order.objects.filter(created_at__date=target)
    total_orders = orders_qs.count()
    total_revenue = orders_qs.aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0.00")

    payments_qs = Payment.objects.filter(posted_at__date=target)
    total_payments = payments_qs.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    refunds_qs = Refund.objects.filter(
        completed_at__date=target,
        status="completed",
    )
    total_refunds = refunds_qs.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    discrepancy = total_payments - total_refunds - total_revenue

    # Generate CSV
    storage_root = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    reconciliation_dir = os.path.join(storage_root, "reconciliation")
    os.makedirs(reconciliation_dir, exist_ok=True)

    csv_filename = f"reconciliation_{target}.csv"
    csv_path = os.path.join(reconciliation_dir, csv_filename)

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Date", "Total Orders", "Total Revenue",
            "Total Payments", "Total Refunds", "Discrepancy",
        ])
        writer.writerow([
            str(target),
            total_orders,
            str(total_revenue),
            str(total_payments),
            str(total_refunds),
            str(discrepancy),
        ])

        # Detail: orders
        writer.writerow([])
        writer.writerow(["Order Number", "Status", "Total", "Paid", "Patient ID"])
        for order in orders_qs.iterator():
            writer.writerow([
                order.order_number,
                order.status,
                str(order.total_amount),
                str(order.amount_paid),
                str(order.patient_id),
            ])

        # Detail: payments
        writer.writerow([])
        writer.writerow(["Payment ID", "Order Number", "Amount", "Method", "Posted At"])
        for payment in payments_qs.select_related("order").iterator():
            writer.writerow([
                str(payment.id),
                payment.order.order_number,
                str(payment.amount),
                payment.payment_method,
                payment.posted_at.isoformat() if payment.posted_at else "",
            ])

    # Determine if this is a deferred reconciliation (not run by celery_beat same day)
    is_deferred = target < date.today() - timedelta(days=1)

    # Create reconciliation record
    record = DailyReconciliation.objects.create(
        reconciliation_date=target,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_payments=total_payments,
        total_refunds=total_refunds,
        discrepancy=discrepancy,
        csv_file_path=csv_path,
        generated_by="celery_beat",
        is_deferred=is_deferred,
    )

    logger.info(
        "Reconciliation generated: date=%s orders=%d revenue=%s payments=%s refunds=%s discrepancy=%s",
        target,
        total_orders,
        total_revenue,
        total_payments,
        total_refunds,
        discrepancy,
    )

    try:
        from apps.audit.service import create_audit_entry

        create_audit_entry(
            event_type="financial_reconciliation_generated",
            user=None,
            username_snapshot="celery_beat",
            client_ip="",
            workstation_id="",
            target_model="DailyReconciliation",
            target_id=str(record.id),
            target_repr=f"Reconciliation {target}",
            field_changes={},
            extra_data={
                "reconciliation_date": str(target),
                "total_orders": total_orders,
                "total_revenue": str(total_revenue),
                "total_payments": str(total_payments),
                "total_refunds": str(total_refunds),
                "discrepancy": str(discrepancy),
                "is_deferred": is_deferred,
                "trigger": "generate_daily_reconciliation",
            },
        )
    except Exception:
        logger.exception(
            "Failed to write audit entry for reconciliation %s", target,
        )

    return {
        "status": "generated",
        "date": str(target),
        "record_id": str(record.id),
    }


@shared_task(name="apps.financials.tasks.check_deferred_reconciliation")
def check_deferred_reconciliation():
    """
    Check the last 7 days for missing reconciliation records and generate
    each one.  Called on user login to catch up after offline periods.
    """
    from apps.financials.models import DailyReconciliation

    today = date.today()
    generated = []

    for days_ago in range(1, 8):
        target = today - timedelta(days=days_ago)

        if not DailyReconciliation.objects.filter(reconciliation_date=target).exists():
            logger.info(
                "Missing reconciliation for %s, generating deferred report.",
                target,
            )
            result = generate_daily_reconciliation(str(target))
            generated.append(str(target))

    if generated:
        logger.info(
            "Deferred reconciliation complete: generated %d report(s) for %s",
            len(generated),
            ", ".join(generated),
        )

    return {"generated_dates": generated, "count": len(generated)}
