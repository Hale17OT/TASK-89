"""Enforces idle and absolute session timeouts."""
import logging
import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse

logger = logging.getLogger("medrights.auth")


class SessionTimeoutMiddleware:
    """
    Enforces:
    - 15-minute idle timeout (MEDRIGHTS_IDLE_TIMEOUT_SECONDS)
    - 8-hour absolute limit (MEDRIGHTS_ABSOLUTE_SESSION_LIMIT)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        now = time.time()
        session = request.session

        # Check absolute timeout
        created = session.get("_session_created")
        if created and (now - created) > settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT:
            logger.info(
                "Session expired (absolute limit)",
                extra={"user_id": request.user.pk, "username": request.user.username},
            )
            logout(request)
            return JsonResponse(
                {
                    "error": "session_expired",
                    "message": "Your session has expired. Please log in again.",
                    "reason": "absolute",
                    "status_code": 401,
                },
                status=401,
            )

        # Check idle timeout
        last_activity = session.get("_last_activity")
        if last_activity and (now - last_activity) > settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS:
            logger.info(
                "Session expired (idle timeout)",
                extra={"user_id": request.user.pk, "username": request.user.username},
            )
            logout(request)
            return JsonResponse(
                {
                    "error": "session_expired",
                    "message": "Your session has expired due to inactivity.",
                    "reason": "idle",
                    "status_code": 401,
                },
                status=401,
            )

        # Update timestamps
        session["_last_activity"] = now
        if "_session_created" not in session:
            session["_session_created"] = now

        return self.get_response(request)
