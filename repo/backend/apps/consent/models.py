"""Consent models: Consent and ConsentScope."""
import uuid
from datetime import date

from django.conf import settings
from django.db import models

from domain.services.consent_service import compute_consent_status


class Consent(models.Model):
    """
    Patient consent record tracking authorisation for data use,
    treatment, media use, or third-party sharing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "mpi.Patient",
        on_delete=models.PROTECT,
        related_name="consents",
    )
    purpose = models.CharField(max_length=200)

    # Who granted it
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_consents",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    # Date range
    effective_date = models.DateField()
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Null means the consent is indefinite.",
    )

    # Revocation
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="revoked_consents",
    )
    revocation_reason = models.TextField(blank=True, default="")

    # Physical copy tracking
    physical_copy_on_file = models.BooleanField(default=False)
    physical_copy_warning_shown = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consents"
        ordering = ["-granted_at"]

    def __str__(self) -> str:
        return f"Consent {self.id} ({self.purpose}) for patient {self.patient_id}"

    @property
    def status(self) -> str:
        """Computed status: 'active', 'expired', or 'revoked'."""
        return compute_consent_status(
            is_revoked=self.is_revoked,
            revoked_at=self.revoked_at,
            expiration_date=self.expiration_date,
            effective_date=self.effective_date,
        )


class ConsentScope(models.Model):
    """
    Fine-grained scope entries attached to a consent -- e.g. which
    data fields, actions, media uses, or third parties are covered.
    """

    SCOPE_TYPE_CHOICES = [
        ("data_field", "Data Field"),
        ("action", "Action"),
        ("media_use", "Media Use"),
        ("third_party", "Third Party"),
    ]

    id = models.BigAutoField(primary_key=True)
    consent = models.ForeignKey(
        Consent,
        on_delete=models.CASCADE,
        related_name="scopes",
    )
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPE_CHOICES)
    scope_value = models.CharField(max_length=200)

    class Meta:
        db_table = "consent_scopes"

    def __str__(self) -> str:
        return f"{self.scope_type}:{self.scope_value}"
