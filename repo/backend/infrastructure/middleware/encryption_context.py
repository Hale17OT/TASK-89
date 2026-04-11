"""Verifies encryption subsystem is initialized before processing requests."""
import logging

from django.http import JsonResponse

logger = logging.getLogger("medrights")

EXEMPT_PATHS = [
    "/api/v1/health/",
]


class EncryptionContextMiddleware:
    """
    Check that the master encryption key is available.
    If not, return 503 for all non-exempt paths.
    In this Docker-first system, the key is loaded from environment
    variables at startup, so this should always pass.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in EXEMPT_PATHS:
            return self.get_response(request)

        from infrastructure.encryption.service import encryption_service

        if not encryption_service.is_initialized():
            logger.error("Encryption service not initialized")
            return JsonResponse(
                {
                    "error": "encryption_not_ready",
                    "message": "Encryption service is not initialized. Contact administrator.",
                    "status_code": 503,
                },
                status=503,
            )

        return self.get_response(request)
