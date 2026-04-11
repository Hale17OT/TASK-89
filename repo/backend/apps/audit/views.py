"""Audit views: list, detail, chain verification, and log purge."""
import json
import logging
import os
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin

from .models import AuditArchiveSegment, AuditEntry
from .serializers import AuditEntryFilterSerializer, AuditEntrySerializer
from .service import verify_audit_chain

logger = logging.getLogger("medrights.audit")


class IsAdminOrCompliance(BasePermission):
    """Only users with 'admin' or 'compliance' role may access."""

    message = "Administrator or compliance officer privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "compliance")
        )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrCompliance])
def audit_list(request):
    """
    GET /api/v1/audit/entries/

    Paginated, filterable list of audit entries.
    Defaults to the last 180 days if no date filters are provided.
    Admin + compliance only.
    """
    filter_ser = AuditEntryFilterSerializer(data=request.query_params)
    filter_ser.is_valid(raise_exception=True)
    filters = filter_ser.validated_data

    queryset = AuditEntry.objects.select_related("user").filter(
        is_archived=False
    ).order_by("-created_at")

    # Default date range: last 180 days.
    from_date = filters.get("from_date", timezone.now() - timedelta(days=180))
    to_date = filters.get("to_date", timezone.now())
    queryset = queryset.filter(created_at__gte=from_date, created_at__lte=to_date)

    if filters.get("event_type"):
        queryset = queryset.filter(event_type=filters["event_type"])

    if filters.get("user_id"):
        queryset = queryset.filter(user_id=filters["user_id"])

    if filters.get("target_model"):
        queryset = queryset.filter(target_model=filters["target_model"])

    # Manual pagination.
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    page_size = min(page_size, 100)
    start = (page - 1) * page_size
    end = start + page_size
    total = queryset.count()

    entries = queryset[start:end]
    serializer = AuditEntrySerializer(entries, many=True)

    return Response({
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": serializer.data,
    })


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrCompliance])
def audit_detail(request, pk):
    """
    GET /api/v1/audit/entries/{id}/

    Retrieve a single audit entry.
    """
    try:
        entry = AuditEntry.objects.select_related("user").get(pk=pk)
    except AuditEntry.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Audit entry not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(AuditEntrySerializer(entry).data)


# ---------------------------------------------------------------------------
# Chain verification
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def audit_verify_chain(request):
    """
    POST /api/v1/audit/verify-chain/

    Trigger a full hash-chain verification of the audit log.
    Admin only.
    """
    is_valid, broken_at_id, total_checked = verify_audit_chain()

    request._audit_context = {
        "event_type": "break_glass_review",
        "target_model": "AuditEntry",
        "target_repr": f"Chain verification: valid={is_valid}, checked={total_checked}",
        "extra_data": {
            "is_valid": is_valid,
            "broken_at_id": broken_at_id,
            "total_checked": total_checked,
        },
    }

    return Response({
        "is_valid": is_valid,
        "broken_at_id": broken_at_id,
        "total_checked": total_checked,
    })


# ---------------------------------------------------------------------------
# Purge
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def audit_purge(request):
    """
    POST /api/v1/audit/purge/

    Delete audit entries older than 7 years.
    Requires admin role + active sudo mode (action_class=log_purge).

    Accepts ``before_date`` in the request body.  The date must be at
    least 7 years in the past to prevent accidental deletion of recent
    records.
    """
    # Sudo check.
    if "log_purge" not in getattr(request, "sudo_actions", set()):
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

    before_date_raw = request.data.get("before_date")
    if not before_date_raw:
        return Response(
            {
                "error": "validation_error",
                "message": "The 'before_date' field is required.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    from django.utils.dateparse import parse_datetime

    before_date = parse_datetime(str(before_date_raw))
    if before_date is None:
        return Response(
            {
                "error": "validation_error",
                "message": "Invalid date format. Use ISO 8601 (e.g. 2019-01-01T00:00:00Z).",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure the cutoff is at least 7 years in the past.
    seven_years_ago = timezone.now() - timedelta(days=7 * 365)
    if before_date > seven_years_ago:
        return Response(
            {
                "error": "validation_error",
                "message": "before_date must be at least 7 years in the past.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    entries_qs = AuditEntry.objects.filter(created_at__lt=before_date).order_by("id")
    count = entries_qs.count()

    if count == 0:
        return Response({
            "message": "No audit entries found before the specified date.",
            "deleted_count": 0,
        })

    # --- Archive entries to JSONL before deletion ---
    storage_root = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    archive_dir = os.path.join(storage_root, "audit_archive")
    os.makedirs(archive_dir, exist_ok=True)

    archive_filename = f"{before_date.date().isoformat()}.jsonl"
    archive_relative = os.path.join("audit_archive", archive_filename)
    archive_absolute = os.path.join(storage_root, archive_relative)

    last_entry = None
    with open(archive_absolute, "w", encoding="utf-8") as f:
        for entry in entries_qs.iterator(chunk_size=1000):
            record = {
                "id": entry.pk,
                "entry_hash": entry.entry_hash,
                "previous_hash": entry.previous_hash,
                "event_type": entry.event_type,
                "user_id": str(entry.user_id) if entry.user_id else None,
                "username_snapshot": entry.username_snapshot,
                "client_ip": str(entry.client_ip) if entry.client_ip else "",
                "workstation_id": entry.workstation_id,
                "target_model": entry.target_model,
                "target_id": entry.target_id,
                "target_repr": entry.target_repr,
                "field_changes": entry.field_changes,
                "extra_data": entry.extra_data,
                "created_at": entry.created_at.isoformat(),
            }
            f.write(json.dumps(record, default=str) + "\n")
            last_entry = entry

    # Record the segment boundary hash so chain verification can bridge the gap
    segment = AuditArchiveSegment.objects.create(
        segment_end_entry_id=last_entry.pk,
        segment_end_hash=last_entry.entry_hash,
        archive_file=archive_relative,
        entries_count=count,
        before_date=before_date,
        purged_by=request.user,
    )

    # Now delete the archived entries
    deleted_count, _ = entries_qs.delete()

    logger.warning(
        "Audit log purge executed",
        extra={
            "purged_by": request.user.username,
            "before_date": str(before_date),
            "deleted_count": deleted_count,
            "archive_file": archive_relative,
            "segment_id": segment.pk,
        },
    )

    request._audit_context = {
        "event_type": "log_purge",
        "target_model": "AuditEntry",
        "target_repr": f"Purged {deleted_count} entries before {before_date}",
        "extra_data": {
            "before_date": str(before_date),
            "deleted_count": deleted_count,
            "archive_file": archive_relative,
            "segment_end_hash": last_entry.entry_hash,
        },
    }

    return Response({
        "message": f"Purged {deleted_count} audit entries older than {before_date.date()}.",
        "deleted_count": deleted_count,
        "archive_file": archive_relative,
    })
