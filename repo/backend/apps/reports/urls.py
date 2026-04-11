"""Reports & Outbox URL configuration."""
from django.urls import path

from . import views

urlpatterns = [
    # Subscriptions
    path("subscriptions/", views.subscription_list_create, name="subscription-list-create"),
    path("subscriptions/<uuid:pk>/", views.subscription_detail, name="subscription-detail"),
    path("subscriptions/<uuid:pk>/run-now/", views.subscription_run_now, name="subscription-run-now"),

    # Outbox
    path("outbox/", views.outbox_list, name="outbox-list"),
    path("outbox/<uuid:pk>/", views.outbox_detail, name="outbox-detail"),
    path("outbox/<uuid:pk>/download/", views.outbox_download, name="outbox-download"),
    path("outbox/<uuid:pk>/retry/", views.outbox_retry, name="outbox-retry"),
    path("outbox/<uuid:pk>/acknowledge/", views.outbox_acknowledge, name="outbox-acknowledge"),

    # Dashboard
    path("dashboard/", views.report_dashboard, name="report-dashboard"),
]
