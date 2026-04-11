"""MPI models: Patient (encrypted PII) and BreakGlassLog."""
import uuid

from django.conf import settings
from django.db import models


class Patient(models.Model):
    """
    Master Patient Index record.

    All PII fields are stored as AES-256-GCM ciphertext in BinaryField
    columns.  Searchable fields (MRN, SSN) also have an HMAC-SHA256
    hash column that enables exact-match lookup without decryption.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # MRN -- encrypted at rest (AES-256-GCM).  The search hash enables
    # HMAC-based lookup without decryption.
    mrn_encrypted = models.BinaryField()
    mrn_search_hash = models.CharField(max_length=64, unique=True, db_index=True)

    # SSN (optional) -- encrypted at rest
    ssn_encrypted = models.BinaryField(null=True, blank=True)
    ssn_search_hash = models.CharField(
        max_length=64, null=True, blank=True, unique=True,
    )

    # Encrypted PII fields
    first_name_encrypted = models.BinaryField()
    last_name_encrypted = models.BinaryField()
    date_of_birth_encrypted = models.BinaryField()
    phone_encrypted = models.BinaryField(null=True, blank=True)
    email_encrypted = models.BinaryField(null=True, blank=True)
    address_encrypted = models.BinaryField(null=True, blank=True)

    # Non-sensitive demographic
    gender = models.CharField(max_length=20, blank=True, default="")

    # Key management
    encryption_key_version = models.SmallIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patients"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Patient {self.mrn_search_hash[:8]}..."


class BreakGlassLog(models.Model):
    """
    Records every break-glass access event -- when a user overrides
    normal masking to view unencrypted patient PII.
    """

    JUSTIFICATION_CATEGORIES = [
        ("emergency", "Emergency"),
        ("treatment", "Treatment"),
        ("legal", "Legal"),
        ("admin", "Administrative"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="break_glass_logs",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="break_glass_logs",
    )
    justification = models.TextField()
    justification_category = models.CharField(
        max_length=20,
        choices=JUSTIFICATION_CATEGORIES,
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    fields_accessed = models.JSONField(
        default=list,
        help_text="List of field names that were unmasked.",
    )
    ip_address = models.GenericIPAddressField()
    workstation_id = models.CharField(max_length=100)

    class Meta:
        db_table = "break_glass_logs"
        ordering = ["-accessed_at"]

    def __str__(self) -> str:
        return (
            f"BreakGlass by {self.user_id} on patient {self.patient_id} "
            f"at {self.accessed_at}"
        )
