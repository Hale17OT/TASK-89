"""Workstation-based login throttling and blacklist enforcement."""
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger("medrights.auth")

LOGIN_PATH = "/api/v1/auth/login/"


class WorkstationThrottleMiddleware:
    """
    On all requests: check if workstation is blacklisted (403).
    On login attempts: enforce 5 failures / 10 min / workstation throttle.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        workstation_id = request.headers.get("X-Workstation-ID", "")
        request.workstation_id = workstation_id

        if not workstation_id:
            if request.path == LOGIN_PATH and request.method == "POST":
                return JsonResponse(
                    {
                        "error": "workstation_id_required",
                        "message": "X-Workstation-ID header is required.",
                        "status_code": 400,
                    },
                    status=400,
                )
            # Allow unauthenticated endpoints without workstation ID (health, prefill)
            # For session-authenticated requests, require it to enforce blacklist.
            # Note: check the session cookie, not request.user, because DRF's
            # force_authenticate (used in tests) doesn't set the Django-level user.
            has_session = bool(request.COOKIES.get("medrights_session") or request.COOKIES.get("sessionid"))
            django_authed = hasattr(request, "user") and getattr(request.user, "is_authenticated", False)
            if has_session or django_authed:
                return JsonResponse(
                    {
                        "error": "workstation_id_required",
                        "message": "X-Workstation-ID header is required for authenticated requests.",
                        "status_code": 400,
                    },
                    status=400,
                )
            return self.get_response(request)

        # Check blacklist
        from apps.accounts.models import WorkstationBlacklist

        client_ip = self._get_client_ip(request)
        request.client_ip = client_ip

        blacklisted = WorkstationBlacklist.objects.filter(
            client_ip=client_ip,
            workstation_id=workstation_id,
            is_active=True,
        ).first()

        if blacklisted:
            logger.warning(
                "Blacklisted workstation attempted access",
                extra={
                    "workstation_id": workstation_id,
                    "client_ip": client_ip,
                    "path": request.path,
                },
            )
            return JsonResponse(
                {
                    "error": "workstation_blacklisted",
                    "message": "This workstation has been blacklisted. Contact an administrator.",
                    "status_code": 403,
                },
                status=403,
            )

        # For login attempts, check throttle
        if request.path == LOGIN_PATH and request.method == "POST":
            from apps.accounts.models import LoginAttempt

            window_start = timezone.now() - timezone.timedelta(
                seconds=settings.MEDRIGHTS_FAILED_LOGIN_WINDOW_SECONDS
            )
            failure_count = LoginAttempt.objects.filter(
                client_ip=client_ip,
                workstation_id=workstation_id,
                was_successful=False,
                attempted_at__gte=window_start,
            ).count()

            if failure_count >= settings.MEDRIGHTS_MAX_FAILED_LOGINS:
                logger.warning(
                    "Login throttle exceeded",
                    extra={
                        "workstation_id": workstation_id,
                        "client_ip": client_ip,
                        "failure_count": failure_count,
                    },
                )
                return JsonResponse(
                    {
                        "error": "throttle_exceeded",
                        "message": "Too many failed login attempts. Please wait before trying again.",
                        "retry_after_seconds": settings.MEDRIGHTS_FAILED_LOGIN_WINDOW_SECONDS,
                        "status_code": 429,
                    },
                    status=429,
                )

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request):
        """Extract the real client IP address.

        Only trust the ``X-Real-IP`` header when the direct peer
        (``REMOTE_ADDR``) is a known Docker-internal address, meaning
        the request came through our Nginx reverse proxy.  When the
        backend is reached directly (e.g., host port 8000), the header
        could be spoofed, so we fall back to ``REMOTE_ADDR``.
        """
        remote_addr = request.META.get("REMOTE_ADDR", "0.0.0.0")
        # Docker-internal networks: 172.16-31.x.x, 10.x.x.x, 127.x.x.x
        is_trusted_proxy = (
            remote_addr.startswith("172.")
            or remote_addr.startswith("10.")
            or remote_addr.startswith("127.")
            or remote_addr == "0.0.0.0"
        )
        if is_trusted_proxy:
            return request.META.get("HTTP_X_REAL_IP", remote_addr)
        return remote_addr
