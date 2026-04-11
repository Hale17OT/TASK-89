"""URL configuration for the Media & Originality Engine."""
from django.urls import path

from . import views

urlpatterns = [
    # Media CRUD
    path("upload/", views.media_upload, name="media-upload"),
    path("", views.media_list, name="media-list"),
    path("<uuid:pk>/", views.media_detail, name="media-detail"),
    path("<uuid:pk>/download/", views.media_download, name="media-download"),
    path("<uuid:pk>/watermark/", views.media_watermark, name="media-watermark"),
    path("<uuid:pk>/attach-patient/", views.media_attach_patient, name="media-attach-patient"),
    path(
        "<uuid:pk>/repost/authorize/",
        views.repost_authorize,
        name="media-repost-authorize",
    ),
    # Infringement reports (GET list + POST create on same path)
    path(
        "infringement/",
        views.infringement_list_create,
        name="infringement-list-create",
    ),
    # Infringement detail (GET detail + PATCH update on same path)
    path(
        "infringement/<uuid:pk>/",
        views.infringement_detail_update,
        name="infringement-detail-update",
    ),
]
