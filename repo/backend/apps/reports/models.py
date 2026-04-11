"""Reports & Outbox models: subscriptions, scheduled reports, and delivery queue."""
import uuid

from django.conf import settings
from django.db import models


class ReportType(models.TextChoices):
    DAILY_RECONCILIATION = "daily_reconciliation", "Daily Reconciliation"
    CONSENT_EXPIRY = "consent_expiry", "Consent Expiry"
    BREAK_GLASS_REVIEW = "break_glass_review", "Break Glass Review"
    MEDIA_ORIGINALITY = "media_originality", "Media Originality"
    FINANCIAL_SUMMARY = "financial_summary", "Financial Summary"
    AUDIT_ACTIVITY = "audit_activity", "Audit Activity"


class ScheduleChoice(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"


class OutputFormat(models.TextChoices):
    PDF = "pdf", "PDF"
    EXCEL = "excel", "Excel"
    IMAGE = "image", "Image"


class OutboxStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    GENERATING = "generating", "Generating"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    STALLED = "stalled", "Stalled"


class FileFormat(models.TextChoices):
    PDF = "pdf", "PDF"
    XLSX = "xlsx", "XLSX"
    PNG = "png", "PNG"


class DeliveryTarget(models.TextChoices):
    PRINT_QUEUE = "print_queue", "Print Queue"
    SHARED_FOLDER = "shared_folder", "Shared Folder"


class ReportSubscription(models.Model):
    """A scheduled report subscription that triggers periodic report generation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=100, choices=ReportType.choices)
    schedule = models.CharField(max_length=20, choices=ScheduleChoice.choices)
    output_format = models.CharField(max_length=10, choices=OutputFormat.choices)
    parameters = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_subscriptions",
    )
    run_time = models.TimeField(default="23:59:00")
    run_day_of_week = models.IntegerField(
        null=True,
        blank=True,
        help_text="0=Monday .. 6=Sunday. Null for daily schedules.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.report_type}, {self.schedule})"


class OutboxItem(models.Model):
    """A report delivery task tracked through generation and delivery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        ReportSubscription,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outbox_items",
    )
    report_name = models.CharField(max_length=300)
    file_path = models.CharField(max_length=500, blank=True, default="")
    file_format = models.CharField(max_length=10, choices=FileFormat.choices)
    file_size_bytes = models.BigIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=OutboxStatus.choices,
        default=OutboxStatus.QUEUED,
        db_index=True,
    )
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    last_error = models.TextField(blank=True, default="")
    next_retry_at = models.DateTimeField(null=True, blank=True)

    delivery_target = models.CharField(
        max_length=50,
        choices=DeliveryTarget.choices,
        default=DeliveryTarget.SHARED_FOLDER,
    )
    delivery_target_path = models.CharField(max_length=500, blank=True, default="")

    generated_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    stalled_at = models.DateTimeField(null=True, blank=True)

    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acknowledged_outbox_items",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "outbox_tasks"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Outbox#{self.pk} {self.report_name} [{self.status}]"
