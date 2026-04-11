"""Reports Celery tasks: subscription processing, report generation, delivery."""
import logging
import os
import shutil
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("medrights")


def _storage_root():
    """Return the base storage directory."""
    return getattr(settings, "MEDRIGHTS_STORAGE_ROOT", settings.MEDIA_ROOT)


def _ensure_dir(path: str):
    """Create directory and parents if they do not exist."""
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Process due subscriptions
# ---------------------------------------------------------------------------

@shared_task(name="apps.reports.tasks.process_due_subscriptions")
def process_due_subscriptions():
    """
    Check active subscriptions whose scheduled run time has arrived.
    For each due subscription, create a queued OutboxItem and trigger
    the generate_report task.
    """
    from .models import (
        OutboxItem,
        OutboxStatus,
        ReportSubscription,
        ScheduleChoice,
    )

    now = timezone.now()
    current_time = now.time()
    current_day_of_week = now.weekday()  # 0=Monday

    active_subs = ReportSubscription.objects.filter(is_active=True)
    processed = 0

    for sub in active_subs:
        # Check if the subscription is due.
        if sub.schedule == ScheduleChoice.WEEKLY:
            if sub.run_day_of_week != current_day_of_week:
                continue

        # Check if run_time is within the current 5-minute window
        # (since this task runs every 5 minutes).
        run_dt = datetime.combine(now.date(), sub.run_time)
        window_start = run_dt - timedelta(minutes=5)
        check_dt = datetime.combine(now.date(), current_time)

        if not (window_start <= check_dt <= run_dt):
            continue

        # Avoid duplicate runs: check if an outbox item already exists
        # for this subscription today.
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        already_run = OutboxItem.objects.filter(
            subscription=sub,
            generated_at__gte=today_start,
        ).exists()

        if already_run:
            continue

        # Determine file format.
        format_map = {"pdf": "pdf", "excel": "xlsx", "image": "png"}
        file_format = format_map.get(sub.output_format, "pdf")

        outbox_item = OutboxItem.objects.create(
            subscription=sub,
            report_name=f"{sub.name} - {now.strftime('%Y-%m-%d')}",
            file_format=file_format,
            status=OutboxStatus.QUEUED,
            delivery_target=sub.parameters.get("delivery_target", "shared_folder"),
            delivery_target_path=sub.parameters.get("delivery_path", ""),
        )

        generate_report.delay(str(outbox_item.pk))
        processed += 1

        logger.info(
            "Queued report generation for subscription %s (%s)",
            sub.name,
            sub.pk,
        )

    logger.info("process_due_subscriptions: processed %d subscriptions", processed)


# ---------------------------------------------------------------------------
# 2. Generate report
# ---------------------------------------------------------------------------

@shared_task(
    name="apps.reports.tasks.generate_report",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def generate_report(self, outbox_item_id: str):
    """
    Generate a report file for the given OutboxItem.

    Queries live database data and produces a PDF, XLSX, or PNG
    tailored to the subscription's report_type.
    """
    from .models import OutboxItem, OutboxStatus

    try:
        item = OutboxItem.objects.select_related("subscription").get(pk=outbox_item_id)
    except OutboxItem.DoesNotExist:
        logger.error("generate_report: OutboxItem %s not found", outbox_item_id)
        return

    item.status = OutboxStatus.GENERATING
    item.save(update_fields=["status"])

    try:
        pending_dir = os.path.join(_storage_root(), "outbox", "pending")
        _ensure_dir(pending_dir)

        filename = f"{item.pk}.{item.file_format}"
        file_path = os.path.join(pending_dir, filename)

        if item.file_format == "pdf":
            _generate_pdf(file_path, item)
        elif item.file_format == "xlsx":
            _generate_xlsx(file_path, item)
        elif item.file_format == "png":
            _generate_png(file_path, item)
        else:
            _generate_pdf(file_path, item)

        file_size = os.path.getsize(file_path)

        # Store relative path (relative to storage root).
        relative_path = os.path.join("outbox", "pending", filename)

        item.file_path = relative_path
        item.file_size_bytes = file_size
        item.status = OutboxStatus.QUEUED  # Ready for delivery.
        item.save(update_fields=["file_path", "file_size_bytes", "status"])

        logger.info(
            "Report generated: %s (%d bytes)",
            item.report_name,
            file_size,
        )

        # Trigger delivery.
        deliver_outbox_item.delay(str(item.pk))

    except Exception as exc:
        item.status = OutboxStatus.FAILED
        item.last_error = str(exc)[:2000]
        item.retry_count += 1
        if item.retry_count < item.max_retries:
            item.next_retry_at = timezone.now() + timedelta(minutes=5)
        item.save(update_fields=["status", "last_error", "retry_count", "next_retry_at"])

        logger.exception("Failed to generate report %s", item.report_name)
        raise self.retry(exc=exc)


def _generate_pdf(file_path: str, item):
    """Generate a PDF report with live database data for the given report type."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, item.report_name)

    c.setFont("Helvetica", 12)
    now = timezone.now()
    c.drawString(72, height - 100, f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    report_type = "Unknown"
    if item.subscription:
        report_type = item.subscription.report_type
    c.drawString(72, height - 124, f"Report Type: {report_type}")

    y = height - 170
    c.setFont("Helvetica", 11)

    if report_type == "daily_reconciliation":
        y = _pdf_daily_reconciliation(c, y, now)
    elif report_type == "financial_summary":
        y = _pdf_financial_summary(c, y, now)
    else:
        y = _pdf_generic_content(c, y, now, report_type)

    c.save()


def _pdf_daily_reconciliation(canvas_obj, y, now):
    """Render daily reconciliation data from the database."""
    from apps.financials.models import DailyReconciliation

    today = now.date()
    recent = DailyReconciliation.objects.filter(
        reconciliation_date__gte=today - timedelta(days=30),
    ).order_by("-reconciliation_date")[:10]

    canvas_obj.setFont("Helvetica-Bold", 13)
    canvas_obj.drawString(72, y, "Daily Reconciliation Summary")
    y -= 24

    canvas_obj.setFont("Helvetica", 10)
    if recent.exists():
        canvas_obj.drawString(72, y, f"Showing last {recent.count()} reconciliation records (up to 30 days)")
        y -= 18

        for rec in recent:
            line = (
                f"{rec.reconciliation_date}  |  Orders: {rec.total_orders}  |  "
                f"Revenue: ${rec.total_revenue}  |  Payments: ${rec.total_payments}  |  "
                f"Refunds: ${rec.total_refunds}  |  Discrepancy: ${rec.discrepancy}"
            )
            canvas_obj.drawString(72, y, line)
            y -= 16
    else:
        canvas_obj.drawString(72, y, "No reconciliation records found for the past 30 days.")
        y -= 18

    return y


def _pdf_financial_summary(canvas_obj, y, now):
    """Render financial summary data from the database."""
    from django.db.models import Count, Sum

    from apps.financials.models import Order, Payment

    canvas_obj.setFont("Helvetica-Bold", 13)
    canvas_obj.drawString(72, y, "Financial Summary")
    y -= 24

    canvas_obj.setFont("Helvetica", 10)

    order_stats = Order.objects.aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total_amount"),
        total_paid=Sum("amount_paid"),
    )
    payment_stats = Payment.objects.aggregate(
        total_payments=Count("id"),
        total_payment_amount=Sum("amount"),
    )

    canvas_obj.drawString(72, y, f"Total Orders: {order_stats['total_orders'] or 0}")
    y -= 16
    canvas_obj.drawString(72, y, f"Total Revenue: ${order_stats['total_revenue'] or 0}")
    y -= 16
    canvas_obj.drawString(72, y, f"Total Amount Paid: ${order_stats['total_paid'] or 0}")
    y -= 16
    canvas_obj.drawString(72, y, f"Total Payments: {payment_stats['total_payments'] or 0}")
    y -= 16
    canvas_obj.drawString(72, y, f"Total Payment Amount: ${payment_stats['total_payment_amount'] or 0}")
    y -= 16

    return y


def _pdf_generic_content(canvas_obj, y, now, report_type):
    """Render a summary report with live counts from all major data tables."""
    from apps.financials.models import Order, Payment, Refund
    from apps.media_engine.models import MediaAsset, InfringementReport
    from apps.mpi.models import Patient, BreakGlassLog
    from apps.consent.models import Consent

    canvas_obj.setFont("Helvetica", 10)

    date_from = now - timedelta(days=30)
    date_to = now

    canvas_obj.drawString(72, y, f"Report period: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")
    y -= 20

    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(72, y, "Clinical Data")
    y -= 16
    canvas_obj.setFont("Helvetica", 10)

    canvas_obj.drawString(72, y, f"Active Patients: {Patient.objects.filter(is_active=True).count()}")
    y -= 16
    canvas_obj.drawString(72, y, f"Active Consents: {Consent.objects.filter(is_revoked=False).count()}")
    y -= 16
    canvas_obj.drawString(72, y, f"Break-Glass Accesses (30d): {BreakGlassLog.objects.filter(accessed_at__gte=date_from).count()}")
    y -= 24

    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(72, y, "Media & Compliance")
    y -= 16
    canvas_obj.setFont("Helvetica", 10)

    canvas_obj.drawString(72, y, f"Media Assets: {MediaAsset.objects.filter(is_deleted=False).count()}")
    y -= 16
    original = MediaAsset.objects.filter(originality_status="original", is_deleted=False).count()
    reposted = MediaAsset.objects.filter(originality_status="reposted", is_deleted=False).count()
    disputed = MediaAsset.objects.filter(originality_status="disputed", is_deleted=False).count()
    canvas_obj.drawString(72, y, f"Originality: {original} original, {reposted} reposted, {disputed} disputed")
    y -= 16
    canvas_obj.drawString(72, y, f"Open Infringements: {InfringementReport.objects.filter(status='open').count()}")
    y -= 24

    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(72, y, "Financial Summary")
    y -= 16
    canvas_obj.setFont("Helvetica", 10)

    canvas_obj.drawString(72, y, f"Total Orders: {Order.objects.count()}")
    y -= 16
    canvas_obj.drawString(72, y, f"Total Payments: {Payment.objects.count()}")
    y -= 16
    canvas_obj.drawString(72, y, f"Pending Refunds: {Refund.objects.filter(status='pending').count()}")
    y -= 16

    return y


def _generate_xlsx(file_path: str, item):
    """Generate an Excel workbook with live database data for the given report type."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append(["Report Name", item.report_name])
    ws.append(["Generated", timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")])
    ws.append([])

    report_type = item.subscription.report_type if item.subscription else "unknown"

    if report_type == "financial_summary":
        from django.db.models import Count, Sum
        from apps.financials.models import Order, Payment
        stats = Order.objects.aggregate(
            total_orders=Count("id"), total_revenue=Sum("total_amount"), total_paid=Sum("amount_paid"),
        )
        ws.append(["Metric", "Value"])
        ws.append(["Total Orders", stats["total_orders"] or 0])
        ws.append(["Total Revenue", float(stats["total_revenue"] or 0)])
        ws.append(["Total Paid", float(stats["total_paid"] or 0)])
        ws.append(["Total Payments", Payment.objects.count()])
    elif report_type == "daily_reconciliation":
        from apps.financials.models import DailyReconciliation
        ws.append(["Date", "Orders", "Revenue", "Payments", "Refunds", "Discrepancy"])
        for rec in DailyReconciliation.objects.order_by("-reconciliation_date")[:30]:
            ws.append([str(rec.reconciliation_date), rec.total_orders, float(rec.total_revenue),
                       float(rec.total_payments), float(rec.total_refunds), float(rec.discrepancy)])
    else:
        from apps.mpi.models import Patient
        from apps.media_engine.models import MediaAsset
        from apps.financials.models import Order
        ws.append(["Metric", "Count"])
        ws.append(["Active Patients", Patient.objects.filter(is_active=True).count()])
        ws.append(["Media Assets", MediaAsset.objects.filter(is_deleted=False).count()])
        ws.append(["Orders", Order.objects.count()])
    wb.save(file_path)


def _generate_png(file_path: str, item):
    """Generate a PNG report snapshot with live database summary data."""
    from PIL import Image, ImageDraw, ImageFont

    from apps.financials.models import Order, Payment
    from apps.media_engine.models import MediaAsset
    from apps.mpi.models import Patient

    img = Image.new("RGB", (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_med = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large

    now = timezone.now()

    draw.text((30, 20), item.report_name, fill=(0, 0, 0), font=font_large)
    draw.text((30, 55), f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}", fill=(100, 100, 100), font=font_small)

    # Horizontal rule
    draw.line([(30, 85), (770, 85)], fill=(200, 200, 200), width=1)

    y = 100
    draw.text((30, y), "System Summary", fill=(0, 0, 0), font=font_med)
    y += 30

    metrics = [
        ("Active Patients", Patient.objects.filter(is_active=True).count()),
        ("Media Assets", MediaAsset.objects.filter(is_deleted=False).count()),
        ("Total Orders", Order.objects.count()),
        ("Total Payments", Payment.objects.count()),
        ("Original Media", MediaAsset.objects.filter(originality_status="original", is_deleted=False).count()),
        ("Reposted Media", MediaAsset.objects.filter(originality_status="reposted", is_deleted=False).count()),
    ]

    for label, value in metrics:
        draw.text((30, y), f"{label}:", fill=(60, 60, 60), font=font_small)
        draw.text((250, y), str(value), fill=(0, 0, 0), font=font_small)
        y += 22

    draw.line([(30, y + 10), (770, y + 10)], fill=(200, 200, 200), width=1)
    y += 25
    draw.text((30, y), "MedRights Patient Media & Consent Portal", fill=(150, 150, 150), font=font_small)

    img.save(file_path, "PNG")


# ---------------------------------------------------------------------------
# 3. Delivery adapters
# ---------------------------------------------------------------------------


def _deliver_to_shared_folder(storage: str, source_path: str, filename: str, item):
    """Deliver a report to a shared folder (filesystem copy)."""
    if item.delivery_target_path:
        dest_dir = item.delivery_target_path
    else:
        dest_dir = os.path.join(storage, "outbox", "delivered")

    _ensure_dir(dest_dir)
    dest_path = os.path.join(dest_dir, filename)
    shutil.copy2(source_path, dest_path)
    logger.info("Shared-folder delivery: %s -> %s", filename, dest_dir)


def _deliver_to_print_queue(storage: str, source_path: str, filename: str, item):
    """
    Deliver a report to the local print queue.

    The print queue is a dedicated directory that an external print
    spooler (e.g. CUPS watch folder) monitors for new files.  When a
    file appears, the spooler picks it up and sends it to the configured
    printer.  The application's responsibility ends at placing the file
    in the queue directory.
    """
    if item.delivery_target_path:
        queue_dir = item.delivery_target_path
    else:
        queue_dir = os.path.join(storage, "outbox", "print_queue")

    _ensure_dir(queue_dir)
    dest_path = os.path.join(queue_dir, filename)
    shutil.copy2(source_path, dest_path)
    logger.info("Print-queue delivery: %s -> %s", filename, queue_dir)


# ---------------------------------------------------------------------------
# 4. Deliver outbox item (orchestrator)
# ---------------------------------------------------------------------------

@shared_task(name="apps.reports.tasks.deliver_outbox_item", bind=True, max_retries=3)
def deliver_outbox_item(self, item_id: str):
    """
    Deliver a generated report file to its configured target.

    Supports two delivery targets:
    - shared_folder: copies file to a shared network directory
    - print_queue: copies file to a print spooler watch directory

    Retries up to 3 times on failure; marks as stalled if retries exhaust.
    """
    from .models import OutboxItem, OutboxStatus

    try:
        item = OutboxItem.objects.get(pk=item_id)
    except OutboxItem.DoesNotExist:
        logger.error("deliver_outbox_item: OutboxItem %s not found", item_id)
        return

    if not item.file_path:
        item.status = OutboxStatus.FAILED
        item.last_error = "No file_path set; report not yet generated."
        item.save(update_fields=["status", "last_error"])
        return

    storage = _storage_root()
    source_path = os.path.join(storage, item.file_path)

    if not os.path.isfile(source_path):
        item.status = OutboxStatus.FAILED
        item.last_error = f"Source file not found: {item.file_path}"
        item.retry_count += 1
        if item.retry_count < item.max_retries:
            item.next_retry_at = timezone.now() + timedelta(minutes=5)
        item.save(update_fields=["status", "last_error", "retry_count", "next_retry_at"])
        logger.error("deliver_outbox_item: source file missing for %s", item.pk)
        return

    try:
        filename = os.path.basename(source_path)

        # ── Deliver based on target type ──────────────────────────────
        if item.delivery_target == "print_queue":
            _deliver_to_print_queue(storage, source_path, filename, item)
        else:
            _deliver_to_shared_folder(storage, source_path, filename, item)

        # Archive a copy in the standard delivered dir for dashboard access
        standard_delivered = os.path.join(storage, "outbox", "delivered")
        _ensure_dir(standard_delivered)
        standard_path = os.path.join(standard_delivered, filename)
        if not os.path.isfile(standard_path):
            shutil.copy2(source_path if os.path.isfile(source_path) else os.path.join(standard_delivered, filename), standard_path)

        # Remove from pending
        if os.path.isfile(source_path):
            os.remove(source_path)

        relative_delivered = os.path.join("outbox", "delivered", filename)
        item.file_path = relative_delivered
        item.status = OutboxStatus.DELIVERED
        item.delivered_at = timezone.now()
        item.save(update_fields=["file_path", "status", "delivered_at"])

        logger.info(
            "Report delivered: %s (target=%s, path=%s)",
            item.report_name,
            item.delivery_target,
            item.delivery_target_path or "default",
        )

    except Exception as exc:
        item.status = OutboxStatus.FAILED
        item.last_error = str(exc)[:2000]
        item.retry_count += 1
        if item.retry_count < item.max_retries:
            item.next_retry_at = timezone.now() + timedelta(minutes=5)
        else:
            # Mark as stalled after exhausting retries.
            item.status = OutboxStatus.STALLED
            item.stalled_at = timezone.now()
        item.save(update_fields=[
            "status", "last_error", "retry_count", "next_retry_at", "stalled_at",
        ])

        logger.exception("Failed to deliver report %s", item.report_name)
        if item.retry_count < item.max_retries:
            raise self.retry(exc=exc, countdown=60)


# ---------------------------------------------------------------------------
# 4. Retry failed outbox items
# ---------------------------------------------------------------------------

@shared_task(name="apps.reports.tasks.retry_failed_outbox_items")
def retry_failed_outbox_items():
    """
    Query failed items whose retry_count < max_retries and whose
    next_retry_at has passed, then re-attempt delivery.
    """
    from .models import OutboxItem, OutboxStatus

    now = timezone.now()
    failed_items = OutboxItem.objects.filter(
        status=OutboxStatus.FAILED,
        next_retry_at__lte=now,
    )

    retried = 0
    for item in failed_items:
        if item.retry_count >= item.max_retries:
            # Mark as stalled instead of retrying further.
            item.status = OutboxStatus.STALLED
            item.stalled_at = now
            item.save(update_fields=["status", "stalled_at"])
            logger.warning(
                "Outbox item %s stalled after %d retries",
                item.pk,
                item.retry_count,
            )
            continue

        deliver_outbox_item.delay(str(item.pk))
        retried += 1
        logger.info("Re-queued delivery for outbox item %s", item.pk)

    logger.info("retry_failed_outbox_items: retried %d items", retried)
