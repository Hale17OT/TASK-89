"""Financial views: Orders, Payments, Refunds, Reconciliation."""
import logging
import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsFrontDeskOrAdmin

from .models import DailyReconciliation, Order, Refund
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    PaymentSerializer,
    ReconciliationSerializer,
    RefundApproveSerializer,
    RefundCreateSerializer,
    RefundOutputSerializer,
    RefundProcessSerializer,
)

logger = logging.getLogger("medrights.financials")


# ── Helpers ───────────────────────────────────────────────────────────

def _get_order_or_404(order_id):
    """Retrieve an order by PK or return a 404-style tuple."""
    try:
        return Order.objects.get(pk=order_id), None
    except Order.DoesNotExist:
        return None, Response(
            {
                "error": "not_found",
                "message": "Order not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )


def _get_refund_or_404(refund_id):
    """Retrieve a refund by PK or return a 404-style tuple."""
    try:
        return Refund.objects.select_related("order", "original_payment").get(
            pk=refund_id
        ), None
    except Refund.DoesNotExist:
        return None, Response(
            {
                "error": "not_found",
                "message": "Refund not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )


# ── Orders ────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsFrontDeskOrAdmin])
def order_list_create(request):
    """
    GET  /api/v1/financials/orders/        -- list orders (with filters)
    POST /api/v1/financials/orders/        -- create a new order
    """
    if request.method == "GET":
        queryset = Order.objects.select_related("patient", "created_by")

        # Filters
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        patient_id = request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        total = queryset.count()
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        start = (page - 1) * page_size
        serializer = OrderListSerializer(queryset[start:start + page_size], many=True)

        request._audit_context = {
            "event_type": "financial_order_list",
            "target_model": "Order",
            "target_id": None,
            "target_repr": "Order list query",
        }

        return Response({"count": total, "next": None, "previous": None, "results": serializer.data})

    # POST -- create order
    serializer = OrderCreateSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    order = serializer.save()

    request._audit_context = {
        "event_type": "financial_order_create",
        "target_model": "Order",
        "target_id": str(order.id),
        "target_repr": f"Order {order.order_number} created",
    }

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsFrontDeskOrAdmin])
def order_detail(request, order_id):
    """
    GET /api/v1/financials/orders/{id}/    -- full order detail
    """
    order, err = _get_order_or_404(order_id)
    if err:
        return err

    serializer = OrderDetailSerializer(order)

    request._audit_context = {
        "event_type": "financial_order_view",
        "target_model": "Order",
        "target_id": str(order.id),
        "target_repr": f"Order {order.order_number} viewed",
    }

    return Response(serializer.data)


# ── Payments ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsFrontDeskOrAdmin])
def order_payment(request, order_id):
    """
    POST /api/v1/financials/orders/{id}/payments/   -- record a payment
    """
    order, err = _get_order_or_404(order_id)
    if err:
        return err

    serializer = PaymentSerializer(
        data=request.data,
        context={"request": request, "order": order},
    )
    serializer.is_valid(raise_exception=True)
    payment = serializer.save()

    request._audit_context = {
        "event_type": "financial_payment_create",
        "target_model": "Payment",
        "target_id": str(payment.id) if payment else "idempotent_duplicate",
        "target_repr": f"Payment on order {order.order_number}",
    }

    if payment is None:
        # Idempotent duplicate -- return cached response
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Void Order ────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAdmin])
def order_void(request, order_id):
    """
    POST /api/v1/financials/orders/{id}/void/   -- void an order (admin only)
    """
    order, err = _get_order_or_404(order_id)
    if err:
        return err

    if order.status == "voided":
        return Response(
            {"error": "conflict", "message": "Order is already voided."},
            status=status.HTTP_409_CONFLICT,
        )

    if order.amount_paid > 0:
        return Response(
            {
                "error": "validation_error",
                "message": "Cannot void an order with payments. Process refunds first.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    order.status = "voided"
    order.save()

    request._audit_context = {
        "event_type": "financial_order_void",
        "target_model": "Order",
        "target_id": str(order.id),
        "target_repr": f"Order {order.order_number} voided",
    }

    logger.info("Order voided: order_number=%s by=%s", order.order_number, request.user.id)

    return Response(OrderDetailSerializer(order).data)


# ── Refunds ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFrontDeskOrAdmin])
def refund_list(request):
    """
    GET /api/v1/financials/refunds/   -- list all refunds
    """
    queryset = Refund.objects.select_related(
        "order", "original_payment", "requested_by", "approved_by",
    )

    status_filter = request.query_params.get("status")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    order_id = request.query_params.get("order_id")
    if order_id:
        queryset = queryset.filter(order_id=order_id)

    total = queryset.count()
    page = int(request.query_params.get("page", 1))
    page_size = min(int(request.query_params.get("page_size", 20)), 100)
    start = (page - 1) * page_size
    serializer = RefundOutputSerializer(queryset[start:start + page_size], many=True)

    request._audit_context = {
        "event_type": "financial_refund_list",
        "target_model": "Refund",
        "target_id": None,
        "target_repr": "Refund list query",
    }

    return Response({"count": total, "next": None, "previous": None, "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsFrontDeskOrAdmin])
def refund_create(request, order_id):
    """
    POST /api/v1/financials/orders/{id}/refunds/   -- initiate a refund
    """
    order, err = _get_order_or_404(order_id)
    if err:
        return err

    serializer = RefundCreateSerializer(
        data=request.data,
        context={"request": request, "order": order},
    )
    serializer.is_valid(raise_exception=True)
    refund = serializer.save()

    request._audit_context = {
        "event_type": "financial_refund_create",
        "target_model": "Refund",
        "target_id": str(refund.id),
        "target_repr": f"Refund requested on order {order.order_number}",
    }

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def refund_approve(request, refund_id):
    """
    POST /api/v1/financials/refunds/{id}/approve/   -- admin approve a refund
    """
    refund, err = _get_refund_or_404(refund_id)
    if err:
        return err

    serializer = RefundApproveSerializer(
        data=request.data,
        context={"request": request, "refund": refund},
    )
    serializer.is_valid(raise_exception=True)
    refund = serializer.save()

    request._audit_context = {
        "event_type": "financial_refund_approve",
        "target_model": "Refund",
        "target_id": str(refund.id),
        "target_repr": f"Refund {refund.id} approved on order {refund.order.order_number}",
    }

    return Response(RefundOutputSerializer(refund).data)


@api_view(["POST"])
@permission_classes([IsAdmin])
def refund_process(request, refund_id):
    """
    POST /api/v1/financials/refunds/{id}/process/   -- process a refund
    """
    refund, err = _get_refund_or_404(refund_id)
    if err:
        return err

    serializer = RefundProcessSerializer(
        data=request.data,
        context={"request": request, "refund": refund},
    )
    serializer.is_valid(raise_exception=True)
    refund = serializer.save()

    request._audit_context = {
        "event_type": "financial_refund_process",
        "target_model": "Refund",
        "target_id": str(refund.id),
        "target_repr": f"Refund {refund.id} processed on order {refund.order.order_number}",
    }

    return Response(RefundOutputSerializer(refund).data)


# ── Reconciliation ────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFrontDeskOrAdmin])
def reconciliation_list(request):
    """
    GET /api/v1/financials/reconciliation/   -- list reconciliation records
    """
    queryset = DailyReconciliation.objects.all()

    date_from = request.query_params.get("date_from")
    if date_from:
        queryset = queryset.filter(reconciliation_date__gte=date_from)

    date_to = request.query_params.get("date_to")
    if date_to:
        queryset = queryset.filter(reconciliation_date__lte=date_to)

    total = queryset.count()
    page = int(request.query_params.get("page", 1))
    page_size = min(int(request.query_params.get("page_size", 20)), 100)
    start = (page - 1) * page_size
    serializer = ReconciliationSerializer(queryset[start:start + page_size], many=True)

    request._audit_context = {
        "event_type": "financial_reconciliation_list",
        "target_model": "DailyReconciliation",
        "target_id": None,
        "target_repr": "Reconciliation list query",
    }

    return Response({"count": total, "next": None, "previous": None, "results": serializer.data})


@api_view(["GET"])
@permission_classes([IsFrontDeskOrAdmin])
def reconciliation_detail(request, date):
    """
    GET /api/v1/financials/reconciliation/{date}/   -- single day detail
    """
    try:
        record = DailyReconciliation.objects.get(reconciliation_date=date)
    except DailyReconciliation.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": f"No reconciliation record for {date}.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ReconciliationSerializer(record)

    request._audit_context = {
        "event_type": "financial_reconciliation_view",
        "target_model": "DailyReconciliation",
        "target_id": str(record.id),
        "target_repr": f"Reconciliation for {date}",
    }

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsFrontDeskOrAdmin])
def reconciliation_download(request, date):
    """
    GET /api/v1/financials/reconciliation/{date}/download/?format=csv|pdf
    """
    try:
        record = DailyReconciliation.objects.get(reconciliation_date=date)
    except DailyReconciliation.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": f"No reconciliation record for {date}.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    file_format = request.query_params.get("format", "csv")

    if file_format == "pdf":
        file_path = record.pdf_file_path
        content_type = "application/pdf"
        extension = "pdf"
    else:
        file_path = record.csv_file_path
        content_type = "text/csv"
        extension = "csv"

    if not file_path or not os.path.exists(file_path):
        return Response(
            {
                "error": "not_found",
                "message": f"Reconciliation {extension.upper()} file not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    request._audit_context = {
        "event_type": "financial_reconciliation_download",
        "target_model": "DailyReconciliation",
        "target_id": str(record.id),
        "target_repr": f"Reconciliation {extension.upper()} download for {date}",
    }

    return FileResponse(
        open(file_path, "rb"),
        content_type=content_type,
        as_attachment=True,
        filename=f"reconciliation_{date}.{extension}",
    )
