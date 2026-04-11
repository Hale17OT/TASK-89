"""Financial URL configuration.

All URLs are under /api/v1/financials/ (set by the root URL conf).
"""
from django.urls import path

from . import views

urlpatterns = [
    # ── Orders ────────────────────────────────────────────────────────
    # GET  /api/v1/financials/orders/            -- list orders
    # POST /api/v1/financials/orders/            -- create order
    path("orders/", views.order_list_create, name="order-list-create"),

    # GET  /api/v1/financials/orders/{id}/       -- order detail
    path("orders/<uuid:order_id>/", views.order_detail, name="order-detail"),

    # POST /api/v1/financials/orders/{id}/payments/  -- record payment
    path(
        "orders/<uuid:order_id>/payments/",
        views.order_payment,
        name="order-payment",
    ),

    # POST /api/v1/financials/orders/{id}/void/      -- void order (admin)
    path(
        "orders/<uuid:order_id>/void/",
        views.order_void,
        name="order-void",
    ),

    # POST /api/v1/financials/orders/{id}/refunds/   -- initiate refund
    path(
        "orders/<uuid:order_id>/refunds/",
        views.refund_create,
        name="refund-create",
    ),

    # ── Refunds ───────────────────────────────────────────────────────
    # GET  /api/v1/financials/refunds/               -- list refunds
    path("refunds/", views.refund_list, name="refund-list"),

    # POST /api/v1/financials/refunds/{id}/approve/  -- approve refund (admin)
    path(
        "refunds/<uuid:refund_id>/approve/",
        views.refund_approve,
        name="refund-approve",
    ),

    # POST /api/v1/financials/refunds/{id}/process/  -- process refund (admin)
    path(
        "refunds/<uuid:refund_id>/process/",
        views.refund_process,
        name="refund-process",
    ),

    # ── Reconciliation ────────────────────────────────────────────────
    # GET  /api/v1/financials/reconciliation/            -- list
    path("reconciliation/", views.reconciliation_list, name="reconciliation-list"),

    # GET  /api/v1/financials/reconciliation/{date}/     -- detail
    path(
        "reconciliation/<str:date>/",
        views.reconciliation_detail,
        name="reconciliation-detail",
    ),

    # GET  /api/v1/financials/reconciliation/{date}/download/  -- file download
    path(
        "reconciliation/<str:date>/download/",
        views.reconciliation_download,
        name="reconciliation-download",
    ),
]
