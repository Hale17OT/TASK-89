"""DRF serializers for the Media & Originality Engine."""
import logging
import os
import uuid
from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.media_engine.models import (
    Citation,
    DisputeHistory,
    InfringementReport,
    MediaAsset,
    MediaDerivative,
)
from apps.media_engine.services import (
    check_originality,
    compute_file_hash,
    compute_pixel_hash,
    extract_evidence_metadata,
    validate_file_type,
)
from domain.services.media_service import validate_infringement_transition

logger = logging.getLogger("medrights.media")

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class MediaUploadSerializer(serializers.Serializer):
    """
    Accepts a file upload, fingerprints it, checks originality, and
    creates a MediaAsset record.
    """

    file = serializers.FileField(required=True)
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    consent_id = serializers.UUIDField(required=False, allow_null=True)
    watermark_config = serializers.JSONField(required=False, allow_null=True)

    def validate_file(self, value):
        """Check magic-byte type and size."""
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"File size {value.size} bytes exceeds the 20 MB limit."
            )
        try:
            detected_mime = validate_file_type(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

        # Stash the detected MIME for later use in create()
        value._detected_mime = detected_mime
        return value

    @transaction.atomic
    def create(self, validated_data):
        file_obj = validated_data["file"]
        user = self.context["request"].user
        detected_mime = getattr(file_obj, "_detected_mime", "application/octet-stream")

        # Compute hashes
        try:
            pixel_hash = compute_pixel_hash(file_obj)
        except ValueError as exc:
            raise serializers.ValidationError({"file": str(exc)})
        file_hash = compute_file_hash(file_obj)

        # Originality check
        originality_status, matching_asset = check_originality(pixel_hash)

        # Extract evidence metadata (immutable, set once)
        evidence_metadata = extract_evidence_metadata(file_obj)

        # Build date-based storage path: storage/media/YYYY/MM/
        today = date.today()
        relative_dir = os.path.join("media", str(today.year), f"{today.month:02d}")
        absolute_dir = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, relative_dir)
        os.makedirs(absolute_dir, exist_ok=True)

        # Unique filename
        ext = os.path.splitext(file_obj.name)[1] or ".bin"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = os.path.join(relative_dir, stored_name)
        absolute_path = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, relative_path)

        # Write file to disk
        file_obj.seek(0)
        with open(absolute_path, "wb") as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)

        # Resolve optional FKs
        patient = None
        consent = None
        patient_id = validated_data.get("patient_id")
        consent_id = validated_data.get("consent_id")

        if patient_id:
            from apps.mpi.models import Patient
            try:
                patient = Patient.objects.get(pk=patient_id)
            except Patient.DoesNotExist:
                raise serializers.ValidationError(
                    {"patient_id": "Patient not found."}
                )

        if consent_id:
            from apps.consent.models import Consent
            from domain.services.consent_service import validate_consent_for_media
            from domain.exceptions import ValidationError as DomainValidationError
            try:
                consent = Consent.objects.prefetch_related("scopes").get(pk=consent_id)
            except Consent.DoesNotExist:
                raise serializers.ValidationError(
                    {"consent_id": "Consent record not found."}
                )

            scopes = consent.scopes.all()
            scope_types = [s.scope_type for s in scopes]
            media_use_values = [s.scope_value for s in scopes if s.scope_type == "media_use"]
            try:
                validate_consent_for_media(
                    is_revoked=consent.is_revoked,
                    expiration_date=consent.expiration_date,
                    effective_date=consent.effective_date,
                    scope_types=scope_types,
                    media_use_scope_values=media_use_values,
                    required_media_use="capture_storage",
                    consent_patient_id=str(consent.patient_id) if consent.patient_id else None,
                    target_patient_id=str(patient.pk) if patient else None,
                )
            except DomainValidationError as exc:
                raise serializers.ValidationError({"consent_id": str(exc)})

        asset = MediaAsset.objects.create(
            patient=patient,
            consent=consent,
            original_file=relative_path,
            original_filename=file_obj.name,
            mime_type=detected_mime,
            file_size_bytes=file_obj.size,
            pixel_hash=pixel_hash,
            file_hash=file_hash,
            originality_status=originality_status,
            watermark_settings=validated_data.get("watermark_config"),
            evidence_metadata=evidence_metadata,
            uploaded_by=user,
        )

        return asset


# ---------------------------------------------------------------------------
# Detail / List
# ---------------------------------------------------------------------------

class MediaDetailSerializer(serializers.ModelSerializer):
    """Full detail view of a MediaAsset."""

    patient_id = serializers.UUIDField(source="patient.pk", allow_null=True, read_only=True)
    consent_id = serializers.UUIDField(source="consent.pk", allow_null=True, read_only=True)
    uploaded_by_id = serializers.UUIDField(source="uploaded_by.pk", read_only=True)
    repost_authorized = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "patient_id",
            "consent_id",
            "original_file",
            "watermarked_file",
            "original_filename",
            "mime_type",
            "file_size_bytes",
            "pixel_hash",
            "file_hash",
            "originality_status",
            "watermark_settings",
            "watermark_burned",
            "evidence_metadata",
            "uploaded_by_id",
            "is_deleted",
            "created_at",
            "updated_at",
            "repost_authorized",
        ]
        read_only_fields = fields

    def get_repost_authorized(self, obj):
        """Return whether reposted media has a valid citation + authorization.

        Returns True for ``reposted_authorized`` status (already approved),
        False for ``reposted`` without citation, and None for non-repost states.
        """
        if obj.originality_status == "reposted_authorized":
            return True
        if obj.originality_status == "reposted":
            return Citation.objects.filter(
                media_asset=obj,
                citation_text__isnull=False,
                authorization_file_path__isnull=False,
            ).exclude(citation_text="").exclude(authorization_file_path="").exists()
        return None


class MediaListSerializer(serializers.ModelSerializer):
    """Lightweight list representation."""

    patient_id = serializers.UUIDField(source="patient.pk", allow_null=True, read_only=True)

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "original_filename",
            "originality_status",
            "patient_id",
            "created_at",
            "mime_type",
            "file_size_bytes",
            "watermark_burned",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------

class WatermarkSerializer(serializers.Serializer):
    """Input for server-side watermark burn."""

    clinic_name = serializers.CharField(max_length=200)
    date_stamp = serializers.BooleanField(default=True)
    opacity = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.35)


# ---------------------------------------------------------------------------
# Repost / Citation
# ---------------------------------------------------------------------------

class RepostAuthorizeSerializer(serializers.Serializer):
    """Attach a citation + authorisation document to a media asset."""

    citation_text = serializers.CharField(min_length=20)
    authorization_file = serializers.FileField(required=True)


class CitationSerializer(serializers.ModelSerializer):
    """Read-only citation representation."""

    class Meta:
        model = Citation
        fields = [
            "id",
            "media_asset_id",
            "citation_text",
            "authorization_file_path",
            "approved_by_id",
            "approved_at",
            "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Infringement
# ---------------------------------------------------------------------------

class InfringementCreateSerializer(serializers.Serializer):
    """Create an infringement report. Only compliance / admin roles."""

    media_asset_id = serializers.UUIDField(required=False, allow_null=True)
    screenshot = serializers.FileField(required=False, allow_null=True)
    reference = serializers.CharField(max_length=2048, required=False, allow_null=True)
    notes = serializers.CharField()

    def validate(self, data):
        screenshot = data.get("screenshot")
        reference = data.get("reference")
        if not screenshot and not reference:
            raise serializers.ValidationError(
                "At least one of 'screenshot' or 'reference' must be provided."
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        media_asset = None
        asset_id = validated_data.get("media_asset_id")
        if asset_id:
            try:
                media_asset = MediaAsset.objects.get(pk=asset_id, is_deleted=False)
            except MediaAsset.DoesNotExist:
                raise serializers.ValidationError(
                    {"media_asset_id": "Media asset not found."}
                )

        # Save optional screenshot
        screenshot_path = None
        screenshot_file = validated_data.get("screenshot")
        if screenshot_file:
            today = date.today()
            rel_dir = os.path.join(
                "infringements", str(today.year), f"{today.month:02d}"
            )
            abs_dir = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, rel_dir)
            os.makedirs(abs_dir, exist_ok=True)
            ext = os.path.splitext(screenshot_file.name)[1] or ".bin"
            fname = f"{uuid.uuid4().hex}{ext}"
            screenshot_path = os.path.join(rel_dir, fname)
            abs_path = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, screenshot_path)
            with open(abs_path, "wb") as f:
                for chunk in screenshot_file.chunks():
                    f.write(chunk)

        report = InfringementReport.objects.create(
            media_asset=media_asset,
            reporter=user,
            screenshot_path=screenshot_path,
            reference=validated_data.get("reference"),
            notes=validated_data["notes"],
        )
        return report


class InfringementDetailSerializer(serializers.ModelSerializer):
    """Read-only detail of an infringement report."""

    reporter_id = serializers.UUIDField(source="reporter.pk", read_only=True)
    media_asset_id = serializers.UUIDField(
        source="media_asset.pk", allow_null=True, read_only=True
    )
    assigned_to_id = serializers.UUIDField(
        source="assigned_to.pk", allow_null=True, read_only=True
    )

    class Meta:
        model = InfringementReport
        fields = [
            "id",
            "media_asset_id",
            "reporter_id",
            "screenshot_path",
            "reference",
            "notes",
            "status",
            "resolution_notes",
            "assigned_to_id",
            "opened_at",
            "investigating_at",
            "resolved_at",
            "dismissed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InfringementListSerializer(serializers.ModelSerializer):
    """Lightweight list representation for infringement reports."""

    media_asset_id = serializers.UUIDField(
        source="media_asset.pk", allow_null=True, read_only=True
    )
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = InfringementReport
        fields = [
            "id",
            "media_asset_id",
            "reporter_name",
            "status",
            "notes",
            "opened_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_reporter_name(self, obj):
        if obj.reporter:
            return obj.reporter.full_name or obj.reporter.username
        return None


class InfringementUpdateSerializer(serializers.Serializer):
    """
    Update the status of an infringement report. Validates allowed
    state transitions and creates a DisputeHistory record.
    """

    status = serializers.ChoiceField(
        choices=[c[0] for c in InfringementReport.STATUS_CHOICES],
    )
    notes = serializers.CharField(required=False, default="")

    def validate(self, attrs):
        report = self.context["report"]
        new_status = attrs["status"]

        if not validate_infringement_transition(report.status, new_status):
            raise serializers.ValidationError(
                {
                    "status": (
                        f"Invalid transition from '{report.status}' to "
                        f"'{new_status}'. Allowed targets: "
                        f"{', '.join(sorted(self._allowed_targets(report.status))) or 'none'}."
                    )
                }
            )
        return attrs

    @staticmethod
    def _allowed_targets(current_status: str):
        from domain.services.media_service import VALID_TRANSITIONS
        return VALID_TRANSITIONS.get(current_status, set())

    @transaction.atomic
    def update(self, report, validated_data):
        user = self.context["request"].user
        old_status = report.status
        new_status = validated_data["status"]
        notes = validated_data.get("notes", "")

        # Update report fields
        report.status = new_status
        report.resolution_notes = notes

        now = timezone.now()
        if new_status == "investigating":
            report.investigating_at = now
        elif new_status == "resolved":
            report.resolved_at = now
        elif new_status == "dismissed":
            report.dismissed_at = now

        report.save()

        # Create dispute history record
        DisputeHistory.objects.create(
            report=report,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=notes,
        )

        return report
