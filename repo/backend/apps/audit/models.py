"""Audit system models: tamper-evident audit log with hash chaining."""
from django.conf import settings
from django.db import models


class EventType(models.TextChoices):
    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILURE = "login_failure", "Login Failure"
    LOGOUT = "logout", "Logout"
    SESSION_TIMEOUT = "session_timeout", "Session Timeout"
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    KEY_FIELD_CHANGE = "key_field_change", "Key Field Change"
    EXPORT = "export", "Export"
    CONSENT_GRANTED = "consent_granted", "Consent Granted"
    CONSENT_REVOKED = "consent_revoked", "Consent Revoked"
    BREAK_GLASS = "break_glass", "Break Glass"
    BREAK_GLASS_REVIEW = "break_glass_review", "Break Glass Review"
    APPROVAL = "approval", "Approval"
    MEDIA_UPLOAD = "media_upload", "Media Upload"
    MEDIA_DISPUTE = "media_dispute", "Media Dispute"
    INFRINGEMENT_REPORT = "infringement_report", "Infringement Report"
    PAYMENT_POSTED = "payment_posted", "Payment Posted"
    REFUND_PROCESSED = "refund_processed", "Refund Processed"
    SUDO_MODE_ENTER = "sudo_mode_enter", "Sudo Mode Enter"
    SUDO_MODE_ACTION = "sudo_mode_action", "Sudo Mode Action"
    USER_DISABLED = "user_disabled", "User Disabled"
    WORKSTATION_BLACKLISTED = "workstation_blacklisted", "Workstation Blacklisted"
    WORKSTATION_UNBLOCKED = "workstation_unblocked", "Workstation Unblocked"
    BULK_EXPORT = "bulk_export", "Bulk Export"
    LOG_PURGE = "log_purge", "Log Purge"
    REPORT_GENERATED = "report_generated", "Report Generated"
    REPORT_DELIVERED = "report_delivered", "Report Delivered"
    PASSWORD_CHANGE = "password_change", "Password Change"

    # Auth events
    AUTH_LOGIN = "auth_login", "Auth Login"
    AUTH_LOGOUT = "auth_logout", "Auth Logout"
    AUTH_PASSWORD_CHANGE = "auth_password_change", "Auth Password Change"
    AUTH_SUDO_ACQUIRE = "auth_sudo_acquire", "Auth Sudo Acquire"
    AUTH_SUDO_RELEASE = "auth_sudo_release", "Auth Sudo Release"
    SESSION_REFRESH = "session_refresh", "Session Refresh"
    REMEMBER_DEVICE = "remember_device", "Remember Device"

    # MPI events
    MPI_PATIENT_SEARCH = "mpi_patient_search", "Patient Search"
    MPI_PATIENT_CREATE = "mpi_patient_create", "Patient Create"
    MPI_PATIENT_VIEW = "mpi_patient_view", "Patient View"
    MPI_PATIENT_UPDATE = "mpi_patient_update", "Patient Update"
    MPI_BREAK_GLASS = "mpi_break_glass", "Break Glass Access"

    # Consent events
    CONSENT_LIST = "consent_list", "Consent List"
    CONSENT_CREATE = "consent_create", "Consent Create"
    CONSENT_VIEW = "consent_view", "Consent View"
    CONSENT_REVOKE = "consent_revoke", "Consent Revoke"

    # Media events
    MEDIA_DOWNLOAD = "media_download", "Media Download"
    MEDIA_WATERMARK = "media_watermark", "Media Watermark"
    MEDIA_REPOST_AUTHORIZE = "media_repost_authorize", "Media Repost Authorize"
    MEDIA_INFRINGEMENT_CREATE = "media_infringement_create", "Infringement Create"
    MEDIA_INFRINGEMENT_UPDATE = "media_infringement_update", "Infringement Update"

    # Financial events
    FINANCIAL_ORDER_LIST = "financial_order_list", "Order List"
    FINANCIAL_ORDER_CREATE = "financial_order_create", "Order Create"
    FINANCIAL_ORDER_VIEW = "financial_order_view", "Order View"
    FINANCIAL_ORDER_VOID = "financial_order_void", "Order Void"
    FINANCIAL_PAYMENT_CREATE = "financial_payment_create", "Payment Create"
    FINANCIAL_REFUND_LIST = "financial_refund_list", "Refund List"
    FINANCIAL_REFUND_CREATE = "financial_refund_create", "Refund Create"
    FINANCIAL_REFUND_APPROVE = "financial_refund_approve", "Refund Approve"
    FINANCIAL_REFUND_PROCESS = "financial_refund_process", "Refund Process"
    FINANCIAL_RECONCILIATION_LIST = "financial_reconciliation_list", "Reconciliation List"
    FINANCIAL_RECONCILIATION_VIEW = "financial_reconciliation_view", "Reconciliation View"
    FINANCIAL_RECONCILIATION_DOWNLOAD = "financial_reconciliation_download", "Reconciliation Download"
    FINANCIAL_AUTO_CLOSE = "financial_auto_close", "Auto-Close Unpaid Order"
    FINANCIAL_RECONCILIATION_GENERATED = "financial_reconciliation_generated", "Reconciliation Generated"

    # Media read events
    MEDIA_DETAIL_VIEW = "media_detail_view", "Media Detail View"
    MEDIA_LIST_VIEW = "media_list_view", "Media List View"

    # Report read events
    REPORT_DOWNLOAD = "report_download", "Report Download"
    REPORT_DASHBOARD_VIEW = "report_dashboard_view", "Report Dashboard View"
    OUTBOX_LIST_VIEW = "outbox_list_view", "Outbox List View"
    OUTBOX_DETAIL_VIEW = "outbox_detail_view", "Outbox Detail View"

    # Media attach event
    MEDIA_ATTACH_PATIENT = "media_attach_patient", "Media Attach Patient"

    # User/Admin events
    USER_CREATE = "user_create", "User Create"
    USER_UPDATE = "user_update", "User Update"
    USER_DISABLE = "user_disable", "User Disable"
    USER_ENABLE = "user_enable", "User Enable"
    WORKSTATION_UNBLOCK = "workstation_unblock", "Workstation Unblock"


# Sentinel hash for the genesis entry (no preceding entry).
GENESIS_HASH = "0" * 64


class AuditEntry(models.Model):
    """
    Tamper-evident audit log entry.

    Each entry stores a SHA-256 hash computed from its own canonical JSON
    representation plus the hash of the preceding entry, forming a hash
    chain that can be verified to detect tampering.
    """

    id = models.BigAutoField(primary_key=True)
    entry_hash = models.CharField(max_length=64, db_index=True)
    previous_hash = models.CharField(max_length=64)

    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )
    username_snapshot = models.CharField(max_length=150)

    client_ip = models.GenericIPAddressField(null=True, blank=True)
    workstation_id = models.CharField(max_length=100, blank=True, default="")

    target_model = models.CharField(max_length=100, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    target_repr = models.CharField(max_length=255, blank=True, default="")

    field_changes = models.JSONField(default=dict, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    is_archived = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["target_model", "target_id"]),
        ]

    def __str__(self):
        return (
            f"AuditEntry#{self.pk} {self.event_type} "
            f"by {self.username_snapshot} at {self.created_at}"
        )


class AuditArchiveSegment(models.Model):
    """
    Records a segment boundary when audit entries are archived/purged.
    Stores the last entry hash of the segment so that the chain can be
    verified across archive gaps.
    """

    id = models.BigAutoField(primary_key=True)
    segment_end_entry_id = models.BigIntegerField(
        help_text="ID of the last audit entry in this archived segment."
    )
    segment_end_hash = models.CharField(
        max_length=64,
        help_text="entry_hash of the last entry in the archived segment."
    )
    archive_file = models.CharField(
        max_length=500,
        help_text="Relative path to the JSONL archive file."
    )
    entries_count = models.IntegerField(default=0)
    before_date = models.DateTimeField()
    purged_at = models.DateTimeField(auto_now_add=True)
    purged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    class Meta:
        db_table = "audit_archive_segments"
        ordering = ["-purged_at"]

    def __str__(self):
        return (
            f"AuditArchiveSegment up to entry #{self.segment_end_entry_id} "
            f"({self.entries_count} entries)"
        )
