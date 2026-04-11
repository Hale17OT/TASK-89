"""Reports & Outbox views: subscriptions CRUD, outbox management, dashboard."""
import logging
import os

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsComplianceOrAdmin

from .models import OutboxItem, OutboxStatus, ReportSubscription
from .serializers import (
    OutboxDashboardSerializer,
    OutboxItemSerializer,
    ReportSubscriptionCreateSerializer,
    ReportSubscriptionListSerializer,
)

logger = logging.getLogger("medrights")


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def subscription_list_create(request):
    """
    GET  /api/v1/reports/subscriptions/  -- list (compliance/admin only)
    POST /api/v1/reports/subscriptions/  -- create (admin only)
    """
    if request.method == "GET":
        subscriptions = ReportSubscription.objects.select_related("created_by").all()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)
        start = (page - 1) * page_size
        end = start + page_size
        total = subscriptions.count()

        serializer = ReportSubscriptionListSerializer(
            subscriptions[start:end], many=True
        )
        return Response({
            "count": total,
            "next": None,
            "previous": None,
            "results": serializer.data,
        })

    # POST -- admin only.
    if not IsAdmin().has_permission(request, None):
        return Response(
            {
                "error": "permission_denied",
                "message": "Administrator privileges required to create subscriptions.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ReportSubscriptionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    subscription = serializer.save(created_by=request.user)

    request._audit_context = {
        "event_type": "create",
        "target_model": "ReportSubscription",
        "target_id": str(subscription.pk),
        "target_repr": subscription.name,
    }

    return Response(
        ReportSubscriptionListSerializer(subscription).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def subscription_detail(request, pk):
    """
    GET    /api/v1/reports/subscriptions/{id}/
    PATCH  /api/v1/reports/subscriptions/{id}/  (admin or creator only)
    DELETE /api/v1/reports/subscriptions/{id}/  (admin or creator only -- soft deactivate)
    """
    try:
        subscription = ReportSubscription.objects.select_related("created_by").get(pk=pk)
    except ReportSubscription.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Report subscription not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(ReportSubscriptionListSerializer(subscription).data)

    # PATCH / DELETE require admin or the creator of the subscription.
    is_admin = request.user.role == "admin"
    is_creator = (
        subscription.created_by_id is not None
        and subscription.created_by_id == request.user.pk
    )
    if not (is_admin or is_creator):
        return Response(
            {
                "error": "permission_denied",
                "message": "Administrator privileges or subscription ownership required.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "PATCH":
        serializer = ReportSubscriptionCreateSerializer(
            subscription, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        request._audit_context = {
            "event_type": "update",
            "target_model": "ReportSubscription",
            "target_id": str(subscription.pk),
            "target_repr": subscription.name,
            "field_changes": request.data,
        }

        return Response(ReportSubscriptionListSerializer(subscription).data)

    # DELETE -- soft-deactivate.
    subscription.is_active = False
    subscription.save(update_fields=["is_active", "updated_at"])

    request._audit_context = {
        "event_type": "update",
        "target_model": "ReportSubscription",
        "target_id": str(subscription.pk),
        "target_repr": f"Deactivated: {subscription.name}",
    }

    return Response({"message": "Subscription deactivated."})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_run_now(request, pk):
    """
    POST /api/v1/reports/subscriptions/{id}/run-now/

    Trigger immediate report generation. Admin only.
    """
    try:
        subscription = ReportSubscription.objects.get(pk=pk)
    except ReportSubscription.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Report subscription not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Determine file format based on output_format.
    format_map = {"pdf": "pdf", "excel": "xlsx", "image": "png"}
    file_format = format_map.get(subscription.output_format, "pdf")

    outbox_item = OutboxItem.objects.create(
        subscription=subscription,
        report_name=f"{subscription.name} (manual run)",
        file_format=file_format,
        status=OutboxStatus.QUEUED,
        delivery_target=subscription.parameters.get("delivery_target", "shared_folder"),
        delivery_target_path=subscription.parameters.get("delivery_path", ""),
    )

    # Trigger async generation.
    try:
        from .tasks import generate_report
        generate_report.delay(str(outbox_item.pk))
    except Exception:
        logger.exception("Failed to enqueue generate_report task")

    request._audit_context = {
        "event_type": "report_generated",
        "target_model": "ReportSubscription",
        "target_id": str(subscription.pk),
        "target_repr": f"Manual run: {subscription.name}",
        "extra_data": {"outbox_item_id": str(outbox_item.pk)},
    }

    return Response(
        {
            "message": "Report generation queued.",
            "outbox_item": OutboxItemSerializer(outbox_item).data,
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def outbox_list(request):
    """
    GET /api/v1/reports/outbox/

    List outbox items, optionally filtered by status.
    Admin and compliance only.
    """
    queryset = OutboxItem.objects.select_related(
        "subscription", "acknowledged_by"
    ).all()

    status_filter = request.query_params.get("status")
    if status_filter and status_filter in OutboxStatus.values:
        queryset = queryset.filter(status=status_filter)

    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    page_size = min(page_size, 100)
    start = (page - 1) * page_size
    end = start + page_size
    total = queryset.count()

    serializer = OutboxItemSerializer(queryset[start:end], many=True)

    request._audit_context = {
        "event_type": "outbox_list_view",
        "target_model": "OutboxItem",
        "target_id": "",
        "target_repr": "Outbox list accessed",
        "extra_data": {"status_filter": status_filter or ""},
    }

    return Response({
        "count": total,
        "next": None,
        "previous": None,
        "results": serializer.data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def outbox_detail(request, pk):
    """
    GET /api/v1/reports/outbox/{id}/

    Admin and compliance only.
    """
    try:
        item = OutboxItem.objects.select_related(
            "subscription", "acknowledged_by"
        ).get(pk=pk)
    except OutboxItem.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Outbox item not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    request._audit_context = {
        "event_type": "outbox_detail_view",
        "target_model": "OutboxItem",
        "target_id": str(item.pk),
        "target_repr": item.report_name,
    }

    return Response(OutboxItemSerializer(item).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def outbox_download(request, pk):
    """
    GET /api/v1/reports/outbox/{id}/download/

    Serve the generated report file for download.
    Admin and compliance only.
    """
    try:
        item = OutboxItem.objects.get(pk=pk)
    except OutboxItem.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Outbox item not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if not item.file_path:
        return Response(
            {
                "error": "file_not_ready",
                "message": "Report file has not been generated yet.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    storage_root = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", settings.MEDIA_ROOT)
    full_path = os.path.join(storage_root, item.file_path)

    if not os.path.isfile(full_path):
        return Response(
            {
                "error": "file_missing",
                "message": "Report file not found on disk.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    content_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "png": "image/png",
    }
    content_type = content_types.get(item.file_format, "application/octet-stream")
    filename = os.path.basename(full_path)

    request._audit_context = {
        "event_type": "report_download",
        "target_model": "OutboxItem",
        "target_id": str(item.pk),
        "target_repr": item.report_name,
        "extra_data": {"file_format": item.file_format},
    }

    return FileResponse(
        open(full_path, "rb"),
        content_type=content_type,
        as_attachment=True,
        filename=filename,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def outbox_retry(request, pk):
    """
    POST /api/v1/reports/outbox/{id}/retry/

    Manually retry a failed outbox item. Admin only.
    """
    try:
        item = OutboxItem.objects.get(pk=pk)
    except OutboxItem.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Outbox item not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if item.status not in (OutboxStatus.FAILED, OutboxStatus.STALLED):
        return Response(
            {
                "error": "invalid_status",
                "message": f"Cannot retry item with status '{item.status}'. Only failed or stalled items can be retried.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    item.status = OutboxStatus.QUEUED
    item.last_error = ""
    item.next_retry_at = None
    item.save(update_fields=["status", "last_error", "next_retry_at"])

    # Trigger async delivery.
    try:
        from .tasks import deliver_outbox_item
        deliver_outbox_item.delay(str(item.pk))
    except Exception:
        logger.exception("Failed to enqueue deliver_outbox_item task")

    request._audit_context = {
        "event_type": "report_delivered",
        "target_model": "OutboxItem",
        "target_id": str(item.pk),
        "target_repr": f"Manual retry: {item.report_name}",
    }

    return Response({
        "message": "Retry queued.",
        "outbox_item": OutboxItemSerializer(item).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def outbox_acknowledge(request, pk):
    """
    POST /api/v1/reports/outbox/{id}/acknowledge/

    Acknowledge a stalled outbox item. Admin only.
    """
    try:
        item = OutboxItem.objects.get(pk=pk)
    except OutboxItem.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Outbox item not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if item.status != OutboxStatus.STALLED:
        return Response(
            {
                "error": "invalid_status",
                "message": "Only stalled items can be acknowledged.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    item.acknowledged_by = request.user
    item.acknowledged_at = timezone.now()
    item.save(update_fields=["acknowledged_by", "acknowledged_at"])

    request._audit_context = {
        "event_type": "report_delivered",
        "target_model": "OutboxItem",
        "target_id": str(item.pk),
        "target_repr": f"Acknowledged: {item.report_name}",
    }

    return Response({
        "message": "Outbox item acknowledged.",
        "outbox_item": OutboxItemSerializer(item).data,
    })


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsComplianceOrAdmin])
def report_dashboard(request):
    """
    GET /api/v1/reports/dashboard/

    Counts by outbox status plus recent items.
    Admin and compliance only.
    """
    from django.db.models import Count, Q

    aggregates = OutboxItem.objects.aggregate(
        queued=Count("id", filter=Q(status=OutboxStatus.QUEUED)),
        generating=Count("id", filter=Q(status=OutboxStatus.GENERATING)),
        delivered=Count("id", filter=Q(status=OutboxStatus.DELIVERED)),
        failed=Count("id", filter=Q(status=OutboxStatus.FAILED)),
        stalled=Count("id", filter=Q(status=OutboxStatus.STALLED)),
        total=Count("id"),
    )

    recent_items = OutboxItem.objects.select_related(
        "subscription", "acknowledged_by"
    ).order_by("-generated_at")[:10]

    dashboard_serializer = OutboxDashboardSerializer(aggregates)

    request._audit_context = {
        "event_type": "report_dashboard_view",
        "target_model": "OutboxItem",
        "target_id": "",
        "target_repr": "Report dashboard accessed",
    }

    return Response({
        "queued": aggregates["queued"],
        "generating": aggregates["generating"],
        "delivered": aggregates["delivered"],
        "failed": aggregates["failed"],
        "stalled": aggregates["stalled"],
        "recent": OutboxItemSerializer(recent_items, many=True).data,
    })
