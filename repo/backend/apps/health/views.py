"""Health check endpoint. No authentication required."""
import logging

from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger("medrights")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Returns system health status.
    Checks: database, redis, encryption service, storage.
    Returns 200 if all OK, 503 if any check fails.
    """
    checks = {}
    all_ok = True

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "ok"}
    except Exception as e:
        logger.error("Health check database failure: %s", e)
        checks["database"] = {"status": "error"}
        all_ok = False

    # Redis check
    try:
        import redis as redis_lib
        from django.conf import settings
        r = redis_lib.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        checks["redis"] = {"status": "ok"}
    except Exception as e:
        logger.error("Health check redis failure: %s", e)
        checks["redis"] = {"status": "error"}
        all_ok = False

    # Encryption service check
    try:
        from infrastructure.encryption.service import encryption_service
        if encryption_service.is_initialized():
            checks["encryption"] = {"status": "ok"}
        else:
            logger.error("Health check encryption failure: service not initialized")
            checks["encryption"] = {"status": "error"}
            all_ok = False
    except Exception as e:
        logger.error("Health check encryption failure: %s", e)
        checks["encryption"] = {"status": "error"}
        all_ok = False

    # Storage check
    try:
        from django.conf import settings
        import os
        storage_root = settings.MEDRIGHTS_STORAGE_ROOT
        if os.path.isdir(storage_root) and os.access(storage_root, os.W_OK):
            checks["storage"] = {"status": "ok"}
        else:
            logger.error("Health check storage failure: directory not writable at %s", storage_root)
            checks["storage"] = {"status": "error"}
            all_ok = False
    except Exception as e:
        logger.error("Health check storage failure: %s", e)
        checks["storage"] = {"status": "error"}
        all_ok = False

    status_code = 200 if all_ok else 503

    # Only expose component-level detail to authenticated admin users.
    # Public/Docker healthcheck gets minimal liveness response only.
    is_admin = (
        hasattr(request, "user")
        and request.user.is_authenticated
        and getattr(request.user, "role", "") == "admin"
    )

    body = {
        "status": "ok" if all_ok else "degraded",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat(),
    }
    if is_admin:
        body["checks"] = checks

    return JsonResponse(body, status=status_code)
