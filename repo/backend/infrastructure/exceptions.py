"""Custom DRF exception handler. Never leaks stack traces in production."""
import logging

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("medrights")


def custom_exception_handler(exc, context):
    """
    Format all API errors consistently:
    { "error": "<code>", "message": "<human-readable>", "status_code": N }
    For validation errors, also include "field_errors".
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, "default_code", "error")
        detail = exc.detail if hasattr(exc, "detail") else str(exc)

        # Handle field-level validation errors
        if isinstance(detail, dict):
            body = {
                "error": "validation_error",
                "message": "One or more fields have errors.",
                "status_code": response.status_code,
                "field_errors": detail,
            }
        elif isinstance(detail, list):
            body = {
                "error": error_code,
                "message": " ".join(str(d) for d in detail),
                "status_code": response.status_code,
            }
        else:
            body = {
                "error": error_code,
                "message": str(detail),
                "status_code": response.status_code,
            }

        response.data = body
        return response

    # Unhandled exception -- never leak internals
    logger.exception(
        "Unhandled exception in %s",
        context.get("request", {}).path if hasattr(context.get("request", {}), "path") else "unknown",
        extra={"exc_type": type(exc).__name__},
    )

    if settings.DEBUG:
        raise exc

    return Response(
        {
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again.",
            "status_code": 500,
        },
        status=500,
    )
