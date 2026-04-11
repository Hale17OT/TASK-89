"""Bulk-export views: CSV exports of patients, media, financials.

Every endpoint requires admin role + an active sudo token for the
``bulk_export`` action class.

All exports enforce patient consent: only data linked to patients who
have at least one active (non-revoked, non-expired) consent record is
included.
"""
import csv
import io
import logging
from datetime import date

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.consent.models import Consent
from .permissions import IsAdmin

logger = logging.getLogger("medrights.export")


def _check_bulk_export_sudo(request):
    """Return an error Response if the caller lacks sudo(bulk_export) or confirm, else None."""
    if "bulk_export" not in getattr(request, "sudo_actions", set()):
        return Response(
            {
                "error": "sudo_required",
                "message": "Sudo mode required. Please re-authenticate to perform this action.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if not request.data.get("confirm"):
        return Response(
            {
                "error": "confirmation_required",
                "message": "Set confirm=true to proceed.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _get_consented_patient_ids(required_scope_type: str = "", required_scope_value: str = ""):
    """Return patient IDs with active consent AND matching scope entries.

    Parameters
    ----------
    required_scope_type : str
        The ``ConsentScope.scope_type`` that must be present (e.g. ``"action"``).
    required_scope_value : str
        The ``ConsentScope.scope_value`` that must be present (e.g. ``"data_sharing"``).

    If both are empty, requires any active consent (backward-compatible).
    """
    from apps.consent.models import ConsentScope

    today = date.today()
    qs = Consent.objects.filter(
        is_revoked=False,
        effective_date__lte=today,
    ).filter(Q(expiration_date__isnull=True) | Q(expiration_date__gte=today))

    if required_scope_type and required_scope_value:
        consent_ids_with_scope = ConsentScope.objects.filter(
            scope_type=required_scope_type,
            scope_value=required_scope_value,
        ).values_list("consent_id", flat=True)
        qs = qs.filter(pk__in=consent_ids_with_scope)

    return qs.values_list("patient_id", flat=True).distinct()


def _csv_response(filename: str, header: list, rows):
    """Build an HttpResponse streaming a CSV file."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(buf.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Consent-Verified"] = "true"
    return response


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_export_patients(request):
    """
    POST /api/v1/export/patients/

    Export patient records as CSV with masked PII fields.
    Requires admin + sudo(bulk_export).
    """
    err = _check_bulk_export_sudo(request)
    if err:
        return err

    from apps.mpi.models import Patient

    patients = Patient.objects.filter(is_active=True).order_by("created_at")

    # Only export patients with active consent + data_sharing scope
    consented_patient_ids = _get_consented_patient_ids("action", "data_sharing")
    patients = patients.filter(pk__in=consented_patient_ids)

    header = ["id", "mrn_masked", "name_masked", "gender", "is_active", "created_at"]
    rows = []
    for p in patients.iterator():
        try:
            from infrastructure.encryption.service import encryption_service
            mrn_plain = encryption_service.decrypt_aes_gcm(bytes(p.mrn_encrypted), "patient_pii")
            mrn_masked = mrn_plain[:4] + "****" if len(mrn_plain) > 4 else "****"
        except Exception:
            mrn_masked = p.mrn_search_hash[:8] + "****"
        rows.append([
            str(p.pk),
            mrn_masked,
            "****",
            p.gender,
            p.is_active,
            str(p.created_at),
        ])

    request._audit_context = {
        "event_type": "bulk_export",
        "target_model": "Patient",
        "target_repr": f"Exported {len(rows)} patient records",
    }

    logger.info("Bulk export patients: %d records by %s", len(rows), request.user.username)
    return _csv_response("patients_export.csv", header, rows)


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_export_media(request):
    """
    POST /api/v1/export/media/

    Export media asset metadata as CSV (no actual files).
    Requires admin + sudo(bulk_export).
    """
    err = _check_bulk_export_sudo(request)
    if err:
        return err

    from apps.media_engine.models import MediaAsset

    assets = MediaAsset.objects.filter(is_deleted=False).order_by("created_at")

    # Only include media linked to patients with media_use consent scope
    consented_ids = _get_consented_patient_ids("media_use", "capture_storage")
    assets = assets.filter(Q(patient_id__isnull=True) | Q(patient_id__in=consented_ids))

    header = [
        "id", "original_filename", "mime_type", "file_size_bytes",
        "originality_status", "watermark_burned", "created_at",
    ]
    rows = []
    for a in assets.iterator():
        rows.append([
            str(a.pk),
            a.original_filename,
            a.mime_type,
            a.file_size_bytes,
            a.originality_status,
            a.watermark_burned,
            str(a.created_at),
        ])

    request._audit_context = {
        "event_type": "bulk_export",
        "target_model": "MediaAsset",
        "target_repr": f"Exported {len(rows)} media records",
    }

    logger.info("Bulk export media: %d records by %s", len(rows), request.user.username)
    return _csv_response("media_export.csv", header, rows)


# ---------------------------------------------------------------------------
# Financials
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_export_financials(request):
    """
    POST /api/v1/export/financials/

    Export financial records (orders + payments) as CSV.
    Requires admin + sudo(bulk_export).
    """
    err = _check_bulk_export_sudo(request)
    if err:
        return err

    from apps.financials.models import Order, Payment

    header = [
        "record_type", "id", "order_number", "status", "total_amount",
        "amount_paid", "payment_method", "created_at",
    ]
    rows = []

    # Only include orders linked to patients with data_sharing consent scope
    consented_ids = _get_consented_patient_ids("action", "data_sharing")
    orders = Order.objects.filter(patient_id__in=consented_ids).order_by("created_at")
    for o in orders.iterator():
        rows.append([
            "order",
            str(o.pk),
            o.order_number,
            o.status,
            str(o.total_amount),
            str(o.amount_paid),
            "",
            str(o.created_at),
        ])

    # Only include payments for orders linked to consented patients
    payments = Payment.objects.filter(order__patient_id__in=consented_ids).order_by("posted_at")
    for p in payments.iterator():
        rows.append([
            "payment",
            str(p.pk),
            "",
            "",
            "",
            str(p.amount),
            p.payment_method,
            str(p.posted_at),
        ])

    request._audit_context = {
        "event_type": "bulk_export",
        "target_model": "Financial",
        "target_repr": f"Exported {len(rows)} financial records",
    }

    logger.info("Bulk export financials: %d records by %s", len(rows), request.user.username)
    return _csv_response("financials_export.csv", header, rows)
