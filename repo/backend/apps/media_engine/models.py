"""Media & Originality Engine models."""
import uuid

from django.conf import settings
from django.db import models


class MediaAsset(models.Model):
    """
    Core media record. Stores file paths, hashes for originality
    fingerprinting, watermark state, and immutable evidence metadata.
    """

    ORIGINALITY_CHOICES = [
        ("original", "Original"),
        ("reposted", "Reposted"),
        ("reposted_authorized", "Reposted (Authorized)"),
        ("disputed", "Disputed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "mpi.Patient",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="media_assets",
    )
    consent = models.ForeignKey(
        "consent.Consent",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="media_assets",
    )
    original_file = models.CharField(max_length=500)
    watermarked_file = models.CharField(max_length=500, blank=True, default="")
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    file_size_bytes = models.BigIntegerField()
    pixel_hash = models.CharField(max_length=64, db_index=True)
    file_hash = models.CharField(max_length=64)
    originality_status = models.CharField(
        max_length=20,
        choices=ORIGINALITY_CHOICES,
        default="original",
        db_index=True,
    )
    watermark_settings = models.JSONField(null=True, blank=True)
    watermark_burned = models.BooleanField(default=False)
    evidence_metadata = models.JSONField(default=dict)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_media",
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "media_assets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.originality_status})"


class Citation(models.Model):
    """
    Authorisation citation for reposted media. Stores the text of the
    citation and an optional authorisation document path.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="citations",
    )
    citation_text = models.TextField()
    authorization_file_path = models.CharField(max_length=500, null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_citations",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_citations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Citation for {self.media_asset_id}"


class MediaDerivative(models.Model):
    """
    A derivative (e.g. watermarked copy) of a parent MediaAsset.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="derivatives",
    )
    derivative_path = models.CharField(max_length=500)
    derivative_hash = models.CharField(max_length=64)
    watermark_applied = models.BooleanField(default=False)
    watermark_settings = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_derivatives",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_derivatives"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Derivative of {self.parent_asset_id}"


class InfringementReport(models.Model):
    """
    Tracks potential copyright or originality infringements.
    """

    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="infringement_reports",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_infringements",
    )
    screenshot_path = models.CharField(max_length=500, null=True, blank=True)
    reference = models.CharField(max_length=2048, null=True, blank=True)
    notes = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True,
    )
    resolution_notes = models.TextField(blank=True, default="")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_infringements",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    investigating_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "infringement_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Infringement #{self.pk} ({self.status})"


class DisputeHistory(models.Model):
    """
    Immutable log of state transitions for an InfringementReport.
    """

    id = models.BigAutoField(primary_key=True)
    report = models.ForeignKey(
        InfringementReport,
        on_delete=models.PROTECT,
        related_name="dispute_history",
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dispute_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "dispute_history"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.old_status} -> {self.new_status} on report {self.report_id}"
