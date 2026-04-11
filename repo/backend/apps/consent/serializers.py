"""Consent serializers: create, list, detail, and revoke."""
import logging
from datetime import date

from django.utils import timezone
from rest_framework import serializers

from domain.services.consent_service import (
    compute_consent_status,
    validate_consent_dates,
    validate_revocation,
)
from domain.exceptions import ConflictError, ValidationError as DomainValidationError

from .models import Consent, ConsentScope

logger = logging.getLogger("medrights.consent")


# ── ConsentScopeSerializer ──────────────────────────────────────────

class ConsentScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentScope
        fields = ["id", "scope_type", "scope_value"]
        read_only_fields = ["id"]


# ── ConsentCreateSerializer ─────────────────────────────────────────

class ConsentCreateSerializer(serializers.Serializer):
    """Create a new consent record for a patient."""

    purpose = serializers.CharField(max_length=200)
    effective_date = serializers.DateField()
    expiration_date = serializers.DateField(required=False, allow_null=True)
    physical_copy_on_file = serializers.BooleanField(required=False, default=False)
    scopes = ConsentScopeSerializer(many=True, required=False)

    def validate(self, data):
        effective = data["effective_date"]
        expiration = data.get("expiration_date")

        try:
            validate_consent_dates(effective, expiration)
        except DomainValidationError as exc:
            raise serializers.ValidationError({"expiration_date": str(exc)})

        return data

    def create(self, validated_data):
        scopes_data = validated_data.pop("scopes", [])
        patient = self.context["patient"]
        user = self.context["request"].user

        consent = Consent.objects.create(
            patient=patient,
            granted_by=user,
            purpose=validated_data["purpose"],
            effective_date=validated_data["effective_date"],
            expiration_date=validated_data.get("expiration_date"),
            physical_copy_on_file=validated_data.get("physical_copy_on_file", False),
        )

        for scope in scopes_data:
            ConsentScope.objects.create(consent=consent, **scope)

        logger.info(
            "Consent created: id=%s patient=%s purpose=%s",
            consent.id,
            patient.id,
            consent.purpose,
        )
        return consent

    def to_representation(self, instance):
        return ConsentListSerializer(instance).data


# ── ConsentListSerializer ───────────────────────────────────────────

class ConsentListSerializer(serializers.Serializer):
    """Read-only consent summary."""

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "patient_id": str(instance.patient_id),
            "purpose": instance.purpose,
            "status": instance.status,
            "granted_by": str(instance.granted_by_id),
            "granted_at": instance.granted_at.isoformat() if instance.granted_at else None,
            "effective_date": str(instance.effective_date),
            "expiration_date": str(instance.expiration_date) if instance.expiration_date else None,
            "is_revoked": instance.is_revoked,
            "revoked_at": instance.revoked_at.isoformat() if instance.revoked_at else None,
            "revoked_by": str(instance.revoked_by_id) if instance.revoked_by_id else None,
            "revocation_reason": instance.revocation_reason,
            "physical_copy_on_file": instance.physical_copy_on_file,
            "scopes": ConsentScopeSerializer(instance.scopes.all(), many=True).data,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }


# ── ConsentRevokeSerializer ─────────────────────────────────────────

class ConsentRevokeSerializer(serializers.Serializer):
    """Revoke an existing consent."""

    reason = serializers.CharField(required=False, default="", allow_blank=True)
    physical_copy_warning_acknowledged = serializers.BooleanField(
        required=False, default=False,
    )

    def validate(self, data):
        consent = self.context["consent"]

        try:
            validate_revocation(
                is_revoked=consent.is_revoked,
                physical_copy_on_file=consent.physical_copy_on_file,
                acknowledged_warning=data.get("physical_copy_warning_acknowledged", False),
            )
        except ConflictError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]})
        except DomainValidationError as exc:
            raise serializers.ValidationError(
                {"physical_copy_warning_acknowledged": str(exc)}
            )

        return data

    def save(self):
        consent = self.context["consent"]
        user = self.context["request"].user

        consent.is_revoked = True
        consent.revoked_at = timezone.now()
        consent.revoked_by = user
        consent.revocation_reason = self.validated_data.get("reason") or "Revoked by user"

        if consent.physical_copy_on_file:
            consent.physical_copy_warning_shown = True

        consent.save()

        logger.info(
            "Consent revoked: id=%s patient=%s by=%s",
            consent.id,
            consent.patient_id,
            user.id,
        )
        return consent
