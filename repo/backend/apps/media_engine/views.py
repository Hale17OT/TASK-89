"""Views for the Media & Originality Engine."""
import logging
import os
import uuid
from datetime import date

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsComplianceOrAdmin, IsFrontDeskOrClinicianOrAdmin
from apps.media_engine.models import (
    Citation,
    InfringementReport,
    MediaAsset,
    MediaDerivative,
)
from apps.media_engine.serializers import (
    CitationSerializer,
    InfringementCreateSerializer,
    InfringementDetailSerializer,
    InfringementListSerializer,
    InfringementUpdateSerializer,
    MediaDetailSerializer,
    MediaListSerializer,
    MediaUploadSerializer,
    RepostAuthorizeSerializer,
    WatermarkSerializer,
)
from apps.media_engine.services import (
    apply_watermark,
    compute_file_hash,
)

logger = logging.getLogger("medrights.media")


def _is_compliance_or_admin(user) -> bool:
    """Return True if the user has compliance or admin role."""
    return user.is_authenticated and user.role in ("compliance", "admin")


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_upload(request):
    """
    POST /api/v1/media/upload/
    Upload a media file with fingerprinting and originality check.
    """
    serializer = MediaUploadSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)

    try:
        asset = serializer.save()
    except Exception as exc:
        logger.exception("Media upload failed")
        return Response(
            {
                "error": "upload_failed",
                "message": "File could not be processed. Please check the file format and try again.",
                "status_code": 422,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    request._audit_context = {
        "event_type": "media_upload",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
        "extra_data": {
            "originality_status": asset.originality_status,
            "pixel_hash": asset.pixel_hash,
        },
    }

    return Response(
        MediaDetailSerializer(asset).data,
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_list(request):
    """
    GET /api/v1/media/
    List media assets with optional filters: patient_id, originality_status.
    """
    qs = MediaAsset.objects.filter(is_deleted=False).select_related("patient")

    patient_id = request.query_params.get("patient_id")
    if patient_id:
        qs = qs.filter(patient_id=patient_id)

    originality_status = request.query_params.get("originality_status")
    if originality_status:
        qs = qs.filter(originality_status=originality_status)

    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(original_filename__icontains=search)

    # Simple offset/limit pagination
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    start = (page - 1) * page_size
    end = start + page_size

    total = qs.count()
    assets = qs[start:end]

    request._audit_context = {
        "event_type": "media_list_view",
        "target_model": "MediaAsset",
        "target_id": "",
        "target_repr": "Media list accessed",
        "extra_data": {
            "filters": {
                "patient_id": patient_id or "",
                "originality_status": originality_status or "",
                "search": search,
            },
        },
    }

    return Response({
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": MediaListSerializer(assets, many=True).data,
    })


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_detail(request, pk):
    """
    GET /api/v1/media/{id}/
    Full detail view of a media asset.
    """
    try:
        asset = MediaAsset.objects.select_related(
            "patient", "consent", "uploaded_by"
        ).get(pk=pk, is_deleted=False)
    except MediaAsset.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Media asset not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    request._audit_context = {
        "event_type": "media_detail_view",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
    }

    return Response(MediaDetailSerializer(asset).data)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_download(request, pk):
    """
    GET /api/v1/media/{id}/download/
    Serve the original file with proper content type.
    Checks that consent is not revoked before serving.
    """
    try:
        asset = MediaAsset.objects.select_related("consent").prefetch_related(
            "consent__scopes"
        ).get(pk=pk, is_deleted=False)
    except MediaAsset.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Media asset not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check consent status if the asset is linked to a consent record
    if asset.consent is not None:
        from domain.services.consent_service import validate_consent_for_media
        from domain.exceptions import ValidationError as DomainValidationError

        scopes = list(asset.consent.scopes.all())
        scope_types = [s.scope_type for s in scopes]
        media_use_values = [s.scope_value for s in scopes if s.scope_type == "media_use"]
        try:
            validate_consent_for_media(
                is_revoked=asset.consent.is_revoked,
                expiration_date=asset.consent.expiration_date,
                effective_date=asset.consent.effective_date,
                scope_types=scope_types,
                media_use_scope_values=media_use_values,
                required_media_use="capture_storage",
            )
        except DomainValidationError as exc:
            return Response(
                {
                    "error": "consent_invalid",
                    "message": f"Consent check failed: {exc}",
                    "status_code": 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    # Check repost authorization: reposted media must have a valid citation
    if asset.originality_status == "reposted":
        has_authorization = Citation.objects.filter(
            media_asset=asset,
            citation_text__isnull=False,
            authorization_file_path__isnull=False,
        ).exclude(
            citation_text="",
        ).exclude(
            authorization_file_path="",
        ).exists()

        if not has_authorization:
            return Response(
                {
                    "error": "repost_not_authorized",
                    "message": "This reposted media requires citation and authorization before download.",
                    "status_code": 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    absolute_path = os.path.join(
        settings.MEDRIGHTS_STORAGE_ROOT, asset.original_file
    )

    if not os.path.isfile(absolute_path):
        return Response(
            {
                "error": "file_missing",
                "message": "The file is no longer available on disk.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    request._audit_context = {
        "event_type": "media_download",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
    }

    response = FileResponse(
        open(absolute_path, "rb"),
        content_type=asset.mime_type,
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{asset.original_filename}"'
    )
    return response


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_watermark(request, pk):
    """
    POST /api/v1/media/{id}/watermark/
    Apply a server-side watermark burn to the media asset.
    """
    try:
        asset = MediaAsset.objects.get(pk=pk, is_deleted=False)
    except MediaAsset.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Media asset not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = WatermarkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    config = serializer.validated_data

    source_path = os.path.join(
        settings.MEDRIGHTS_STORAGE_ROOT, asset.original_file
    )

    if not os.path.isfile(source_path):
        return Response(
            {
                "error": "file_missing",
                "message": "The original file is no longer available on disk.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Build watermarked output path
    today = date.today()
    rel_dir = os.path.join(
        "watermarked", str(today.year), f"{today.month:02d}"
    )
    abs_dir = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    ext = os.path.splitext(asset.original_filename)[1] or ".jpg"
    out_name = f"{uuid.uuid4().hex}{ext}"
    relative_output = os.path.join(rel_dir, out_name)
    absolute_output = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, relative_output)

    with transaction.atomic():
        try:
            apply_watermark(source_path, absolute_output, config)
        except Exception as exc:
            logger.exception("Watermark application failed for asset %s", pk)
            return Response(
                {
                    "error": "watermark_failed",
                    "message": "Watermark could not be applied. Please verify the source image and try again.",
                    "status_code": 422,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Compute derivative hash
        with open(absolute_output, "rb") as f:
            derivative_hash = compute_file_hash(f)

        # Create derivative record
        MediaDerivative.objects.create(
            parent_asset=asset,
            derivative_path=relative_output,
            derivative_hash=derivative_hash,
            watermark_applied=True,
            watermark_settings=config,
            created_by=request.user,
        )

        # Update the parent asset
        asset.watermarked_file = relative_output
        asset.watermark_settings = config
        asset.watermark_burned = True
        asset.save(update_fields=[
            "watermarked_file",
            "watermark_settings",
            "watermark_burned",
            "updated_at",
        ])

    request._audit_context = {
        "event_type": "media_watermark",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
        "extra_data": {"watermark_config": config},
    }

    return Response(MediaDetailSerializer(asset).data)


# ---------------------------------------------------------------------------
# Repost / Citation authorisation
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsComplianceOrAdmin])
def repost_authorize(request, pk):
    """
    POST /api/v1/media/{id}/repost/authorize/
    Attach a citation and authorisation document. Compliance/admin only.
    """
    try:
        asset = MediaAsset.objects.get(pk=pk, is_deleted=False)
    except MediaAsset.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Media asset not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = RepostAuthorizeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    auth_file = serializer.validated_data["authorization_file"]

    # Save authorisation file
    today = date.today()
    rel_dir = os.path.join(
        "citations", str(today.year), f"{today.month:02d}"
    )
    abs_dir = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    ext = os.path.splitext(auth_file.name)[1] or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    auth_relative = os.path.join(rel_dir, fname)
    auth_absolute = os.path.join(settings.MEDRIGHTS_STORAGE_ROOT, auth_relative)

    with open(auth_absolute, "wb") as f:
        for chunk in auth_file.chunks():
            f.write(chunk)

    citation = Citation.objects.create(
        media_asset=asset,
        citation_text=serializer.validated_data["citation_text"],
        authorization_file_path=auth_relative,
        approved_by=request.user,
        approved_at=timezone.now(),
    )

    # Transition originality status to "reposted_authorized"
    if asset.originality_status == "reposted":
        asset.originality_status = "reposted_authorized"
        asset.save(update_fields=["originality_status"])

    request._audit_context = {
        "event_type": "media_repost_authorize",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
        "extra_data": {"citation_id": str(citation.pk)},
    }

    return Response(
        CitationSerializer(citation).data,
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Attach to Patient
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def media_attach_patient(request, pk):
    """
    POST /api/v1/media/{id}/attach-patient/
    Link a media asset to a patient.  Accepts ``{ "patient_id": "<uuid>" }``.
    """
    from apps.mpi.models import Patient

    try:
        asset = MediaAsset.objects.select_related("consent").prefetch_related(
            "consent__scopes"
        ).get(pk=pk, is_deleted=False)
    except MediaAsset.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Media asset not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    patient_id = request.data.get("patient_id")
    if not patient_id:
        return Response(
            {
                "error": "validation_error",
                "message": "patient_id is required.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Approval gate: reject disputed media or unauthorized reposts
    if asset.originality_status == "disputed":
        return Response(
            {
                "error": "media_not_approved",
                "message": "Disputed media cannot be attached to patient materials.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if asset.originality_status == "reposted":
        from .models import Citation
        has_auth = Citation.objects.filter(
            media_asset=asset,
        ).exclude(citation_text="").exclude(authorization_file_path="").exists()
        if not has_auth:
            return Response(
                {
                    "error": "media_not_approved",
                    "message": "Reposted media requires citation and authorization before attaching.",
                    "status_code": 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    try:
        patient = Patient.objects.get(pk=patient_id, is_active=True)
    except Patient.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Patient not found or inactive.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Validate consent covers the target patient if a consent is linked
    if asset.consent is not None:
        from domain.services.consent_service import validate_consent_for_media
        from domain.exceptions import ValidationError as DomainValidationError

        scopes = list(asset.consent.scopes.all())
        scope_types = [s.scope_type for s in scopes]
        media_use_values = [s.scope_value for s in scopes if s.scope_type == "media_use"]
        try:
            validate_consent_for_media(
                is_revoked=asset.consent.is_revoked,
                expiration_date=asset.consent.expiration_date,
                effective_date=asset.consent.effective_date,
                scope_types=scope_types,
                media_use_scope_values=media_use_values,
                required_media_use="capture_storage",
                consent_patient_id=str(asset.consent.patient_id) if asset.consent.patient_id else None,
                target_patient_id=str(patient.pk),
            )
        except DomainValidationError as exc:
            return Response(
                {
                    "error": "consent_invalid",
                    "message": f"Consent check failed: {exc}",
                    "status_code": 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    asset.patient = patient
    asset.save(update_fields=["patient", "updated_at"])

    request._audit_context = {
        "event_type": "media_attach_patient",
        "target_model": "MediaAsset",
        "target_id": str(asset.pk),
        "target_repr": asset.original_filename,
        "extra_data": {"patient_id": str(patient.pk)},
    }

    return Response(MediaDetailSerializer(asset).data)


# ---------------------------------------------------------------------------
# Infringement CRUD
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsComplianceOrAdmin])
def infringement_list_create(request):
    """
    GET  /api/v1/media/infringement/  -- list infringement reports
    POST /api/v1/media/infringement/  -- create an infringement report
    Compliance / admin only.
    """
    # -- POST: create -------------------------------------------------------
    if request.method == "POST":
        serializer = InfringementCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        # Transition linked media to disputed status
        if report.media_asset and report.media_asset.originality_status != "disputed":
            report.media_asset.originality_status = "disputed"
            report.media_asset.save(update_fields=["originality_status"])

        request._audit_context = {
            "event_type": "media_infringement_create",
            "target_model": "InfringementReport",
            "target_id": str(report.pk),
            "target_repr": f"Infringement #{report.pk}",
        }

        return Response(
            InfringementDetailSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )

    # -- GET: list ----------------------------------------------------------
    qs = InfringementReport.objects.select_related("media_asset", "reporter").all()

    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)

    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    start = (page - 1) * page_size
    end = start + page_size

    total = qs.count()
    reports = qs[start:end]

    return Response({
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": InfringementListSerializer(reports, many=True).data,
    })


@api_view(["GET", "PATCH"])
@permission_classes([IsComplianceOrAdmin])
def infringement_detail_update(request, pk):
    """
    GET   /api/v1/media/infringement/{id}/  -- detail
    PATCH /api/v1/media/infringement/{id}/  -- update status
    Compliance / admin only.
    """
    try:
        report = InfringementReport.objects.select_related(
            "media_asset", "reporter", "assigned_to"
        ).get(pk=pk)
    except InfringementReport.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Infringement report not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # -- GET: detail --------------------------------------------------------
    if request.method == "GET":
        return Response(InfringementDetailSerializer(report).data)

    # -- PATCH: update status -----------------------------------------------
    serializer = InfringementUpdateSerializer(
        data=request.data,
        context={"request": request, "report": report},
    )
    serializer.is_valid(raise_exception=True)

    old_status = report.status
    new_status = serializer.validated_data["status"]
    report = serializer.update(report, serializer.validated_data)

    # On resolution/dismissal, revert media originality if no other open reports
    if new_status in ("resolved", "dismissed") and report.media_asset:
        other_open = InfringementReport.objects.filter(
            media_asset=report.media_asset,
            status__in=["open", "investigating"],
        ).exclude(pk=report.pk).exists()
        if not other_open:
            # Revert: check if authorized citation exists
            has_authorized_citation = Citation.objects.filter(
                media_asset=report.media_asset,
            ).exclude(citation_text="").exclude(authorization_file_path="").exists()
            has_any_citation = Citation.objects.filter(media_asset=report.media_asset).exists()
            if has_authorized_citation:
                report.media_asset.originality_status = "reposted_authorized"
            elif has_any_citation:
                report.media_asset.originality_status = "reposted"
            else:
                report.media_asset.originality_status = "original"
            report.media_asset.save(update_fields=["originality_status"])

    request._audit_context = {
        "event_type": "media_infringement_update",
        "target_model": "InfringementReport",
        "target_id": str(report.pk),
        "target_repr": f"Infringement #{report.pk}",
        "field_changes": {
            "status": {"old": old_status, "new": report.status},
        },
    }

    return Response(InfringementDetailSerializer(report).data)
