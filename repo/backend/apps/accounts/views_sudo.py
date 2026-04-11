"""Sudo-mode views: acquire, status, release elevated privileges."""
import hashlib
import logging
import secrets
import time

from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SudoToken
from .permissions import IsAdmin
from .serializers import SudoAcquireSerializer

logger = logging.getLogger("medrights.auth")

SUDO_DURATION_SECONDS = 300  # 5 minutes


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def sudo_acquire(request):
    """
    Verify the admin's password and grant a 5-minute scoped sudo token.
    The token is stored both in the DB and in the session so the
    SudoModeMiddleware can populate request.sudo_actions on every request.
    """
    serializer = SudoAcquireSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    password = serializer.validated_data["password"]
    action_class = serializer.validated_data["action_class"]

    if not request.user.check_password(password):
        return Response(
            {
                "error": "invalid_password",
                "message": "Password verification failed.",
                "status_code": 401,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Create token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    now = timezone.now()
    expires_at = now + timezone.timedelta(seconds=SUDO_DURATION_SECONDS)

    SudoToken.objects.create(
        user=request.user,
        session_key=request.session.session_key or "",
        action_class=action_class,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    # Store in session so middleware can read it
    sudo_data = request.session.get("_sudo_tokens", {})
    sudo_data[action_class] = {
        "token_hash": token_hash,
        "expires_at": time.time() + SUDO_DURATION_SECONDS,
    }
    request.session["_sudo_tokens"] = sudo_data

    logger.info(
        "Sudo token acquired",
        extra={
            "user_id": str(request.user.pk),
            "username": request.user.username,
            "action_class": action_class,
        },
    )

    request._audit_context = {
        "event_type": "auth_sudo_acquire",
        "target_model": "SudoToken",
        "target_repr": action_class,
        "extra_data": {"action_class": action_class},
    }

    return Response({
        "action_class": action_class,
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": SUDO_DURATION_SECONDS,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def sudo_status(request):
    """Return the currently active sudo action classes and their expiry."""
    sudo_data = request.session.get("_sudo_tokens", {})
    now = time.time()

    active = []
    for action_class, info in sudo_data.items():
        remaining = info.get("expires_at", 0) - now
        if remaining > 0:
            active.append({
                "action_class": action_class,
                "expires_in_seconds": round(remaining, 1),
            })

    return Response({"active_sudo_actions": active})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def sudo_release(request):
    """Clear all sudo tokens from the current session."""
    request.session["_sudo_tokens"] = {}

    # Also mark DB tokens as used
    session_key = request.session.session_key
    if session_key:
        SudoToken.objects.filter(
            user=request.user,
            session_key=session_key,
            used=False,
        ).update(used=True, used_at=timezone.now())

    request._audit_context = {
        "event_type": "auth_sudo_release",
        "target_model": "SudoToken",
        "target_repr": "all",
    }

    return Response(status=status.HTTP_204_NO_CONTENT)
