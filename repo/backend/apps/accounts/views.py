"""Auth views: login, logout, session, remember-device, guest profiles."""
import hashlib
import logging
import secrets
import time

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    GuestProfile,
    GuestRecentPatient,
    Lockout,
    LoginAttempt,
    RememberDevice,
    WorkstationBlacklist,
)
from .serializers import (
    ChangePasswordSerializer,
    GuestProfileSerializer,
    GuestRecentPatientSerializer,
    LoginSerializer,
    UserInfoSerializer,
)

logger = logging.getLogger("medrights.auth")

REMEMBER_COOKIE_NAME = "medrights_remember"
REMEMBER_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


# ---------------------------------------------------------------------------
# CSRF cookie
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_cookie(request):
    """Return an empty response that sets the CSRF cookie.

    Called by the frontend on initial page load so the login POST
    has a valid CSRF token.
    """
    from django.middleware.csrf import get_token
    get_token(request)  # Forces Django to set the CSRF cookie
    return Response({"detail": "CSRF cookie set"})


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate a user with username + password.
    CSRF is exempt because users have no session to protect at login time.
    The WorkstationThrottleMiddleware already enforces per-workstation
    throttling before this view runs, so we only need to record the
    attempt and handle the result.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]
    remember = serializer.validated_data.get("remember_device", False)

    client_ip = getattr(request, "client_ip", request.META.get("REMOTE_ADDR", "0.0.0.0"))
    workstation_id = getattr(request, "workstation_id", "")

    user = authenticate(request, username=username, password=password)

    if user is None:
        # Record failed attempt
        LoginAttempt.objects.create(
            username_tried=username,
            client_ip=client_ip,
            workstation_id=workstation_id,
            was_successful=False,
            failure_reason="invalid_credentials",
        )

        # Check if this failure triggers a lockout
        _check_lockout_threshold(client_ip, workstation_id)

        return Response(
            {
                "error": "invalid_credentials",
                "message": "Invalid username or password.",
                "status_code": 401,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        LoginAttempt.objects.create(
            username_tried=username,
            client_ip=client_ip,
            workstation_id=workstation_id,
            was_successful=False,
            failure_reason="account_disabled",
        )
        return Response(
            {
                "error": "account_disabled",
                "message": "This account has been disabled. Contact an administrator.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Successful login
    login(request, user)

    now = time.time()
    request.session["_session_created"] = now
    request.session["_last_activity"] = now

    LoginAttempt.objects.create(
        username_tried=username,
        client_ip=client_ip,
        workstation_id=workstation_id,
        was_successful=True,
    )

    logger.info(
        "User logged in",
        extra={
            "user_id": str(user.pk),
            "username": user.username,
            "client_ip": client_ip,
            "workstation_id": workstation_id,
        },
    )

    request._audit_context = {
        "event_type": "auth_login",
        "target_model": "User",
        "target_id": str(user.pk),
        "target_repr": user.username,
    }

    response_data = {
        "user": UserInfoSerializer(user).data,
        "idle_timeout_seconds": settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS,
        "absolute_session_limit": settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT,
    }

    resp = Response(response_data, status=status.HTTP_200_OK)

    # Handle remember-device cookie
    if remember:
        resp = _set_remember_device_cookie(resp, user, workstation_id)

    return resp


def _check_lockout_threshold(client_ip, workstation_id):
    """
    After a failed login, check whether the number of recent failures
    has crossed the lockout threshold.  If so, create a Lockout record.
    Then check whether the number of lockouts in the blacklist window
    has crossed the blacklist threshold.
    """
    window_start = timezone.now() - timezone.timedelta(
        seconds=settings.MEDRIGHTS_FAILED_LOGIN_WINDOW_SECONDS
    )
    recent_failures = LoginAttempt.objects.filter(
        client_ip=client_ip,
        workstation_id=workstation_id,
        was_successful=False,
        attempted_at__gte=window_start,
    ).count()

    if recent_failures >= settings.MEDRIGHTS_MAX_FAILED_LOGINS:
        now = timezone.now()
        lockout_duration = timezone.timedelta(seconds=settings.MEDRIGHTS_LOCKOUT_DURATION_SECONDS)

        # Only create one lockout per lockout window to prevent a single
        # burst of failures from generating multiple lockout records.
        active_lockout = Lockout.objects.filter(
            client_ip=client_ip,
            workstation_id=workstation_id,
            expires_at__gt=now,
        ).exists()

        if not active_lockout:
            Lockout.objects.create(
                client_ip=client_ip,
                workstation_id=workstation_id,
                expires_at=now + lockout_duration,
            )
            logger.warning(
                "Lockout triggered",
                extra={"client_ip": client_ip, "workstation_id": workstation_id},
            )

            # Count distinct lockout events in the blacklist window
            blacklist_window = now - timezone.timedelta(
                seconds=settings.MEDRIGHTS_BLACKLIST_WINDOW_SECONDS
            )
            distinct_lockouts = Lockout.objects.filter(
                client_ip=client_ip,
                workstation_id=workstation_id,
                locked_at__gte=blacklist_window,
            ).count()

            if distinct_lockouts >= settings.MEDRIGHTS_LOCKOUTS_BEFORE_BLACKLIST:
                _blacklist_workstation(client_ip, workstation_id, distinct_lockouts)


def _blacklist_workstation(client_ip, workstation_id, lockout_count):
    """Create or update a blacklist entry for the workstation."""
    entry, created = WorkstationBlacklist.objects.get_or_create(
        client_ip=client_ip,
        workstation_id=workstation_id,
        defaults={
            "lockout_count": lockout_count,
            "blacklisted_at": timezone.now(),
            "is_active": True,
        },
    )
    if not created:
        entry.lockout_count = lockout_count
        entry.blacklisted_at = timezone.now()
        entry.is_active = True
        entry.save(update_fields=["lockout_count", "blacklisted_at", "is_active"])

    logger.critical(
        "Workstation blacklisted",
        extra={
            "client_ip": client_ip,
            "workstation_id": workstation_id,
            "lockout_count": lockout_count,
        },
    )


def _set_remember_device_cookie(response, user, workstation_id):
    """Create a RememberDevice record and attach an HttpOnly cookie."""
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    RememberDevice.objects.create(
        token_hash=token_hash,
        workstation_id=workstation_id,
        username=user.username,
        expires_at=timezone.now() + timezone.timedelta(seconds=REMEMBER_COOKIE_MAX_AGE),
    )

    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        raw_token,
        max_age=REMEMBER_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Log the user out, destroy the session."""
    request._audit_context = {
        "event_type": "auth_logout",
        "target_model": "User",
        "target_id": str(request.user.pk),
        "target_repr": request.user.username,
    }
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Session info / refresh
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_info(request):
    """Return current session metadata and remaining time."""
    now = time.time()
    created = request.session.get("_session_created", now)
    last_activity = request.session.get("_last_activity", now)

    idle_remaining = max(
        0, settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS - (now - last_activity)
    )
    absolute_remaining = max(
        0, settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT - (now - created)
    )

    return Response({
        "user": UserInfoSerializer(request.user).data,
        "idle_remaining_seconds": round(idle_remaining, 1),
        "absolute_remaining_seconds": round(absolute_remaining, 1),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_refresh(request):
    """Reset the idle timer (keep-alive)."""
    now = time.time()
    request.session["_last_activity"] = now
    created = request.session.get("_session_created", now)

    idle_remaining = settings.MEDRIGHTS_IDLE_TIMEOUT_SECONDS
    absolute_remaining = max(
        0, settings.MEDRIGHTS_ABSOLUTE_SESSION_LIMIT - (now - created)
    )

    request._audit_context = {
        "event_type": "session_refresh",
        "target_model": "Session",
        "target_id": request.session.session_key or "",
        "target_repr": f"Session refreshed for {request.user.username}",
    }

    return Response({
        "idle_remaining_seconds": round(idle_remaining, 1),
        "absolute_remaining_seconds": round(absolute_remaining, 1),
    })


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Verify current password, validate & set new password, invalidate other sessions."""
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={"user": request.user},
    )
    serializer.is_valid(raise_exception=True)

    if not request.user.check_password(serializer.validated_data["current_password"]):
        return Response(
            {
                "error": "invalid_password",
                "message": "Current password is incorrect.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(serializer.validated_data["new_password"])
    request.user.last_password_change = timezone.now()
    request.user.save(update_fields=["password", "last_password_change"])

    # Invalidate all other sessions for this user
    current_session_key = request.session.session_key
    _invalidate_other_sessions(request.user, current_session_key)

    # Keep the current session alive after password change
    login(request, request.user)

    request._audit_context = {
        "event_type": "auth_password_change",
        "target_model": "User",
        "target_id": str(request.user.pk),
        "target_repr": request.user.username,
    }

    return Response({"message": "Password changed successfully."})


def _invalidate_other_sessions(user, keep_session_key):
    """Delete all sessions for a user except the current one."""
    all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in all_sessions.iterator():
        try:
            data = session.get_decoded()
            if (
                data.get("_auth_user_id") == str(user.pk)
                and session.session_key != keep_session_key
            ):
                session.delete()
        except Exception:
            continue


# ---------------------------------------------------------------------------
# Remember device
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remember_device(request):
    """Create a remember-device cookie for username pre-fill on subsequent logins."""
    workstation_id = getattr(request, "workstation_id", "") or request.headers.get(
        "X-Workstation-ID", ""
    )

    request._audit_context = {
        "event_type": "remember_device",
        "target_model": "RememberDevice",
        "target_id": workstation_id,
        "target_repr": f"Device remembered for {request.user.username}",
    }

    resp = Response({"message": "Device remembered."})
    resp = _set_remember_device_cookie(resp, request.user, workstation_id)
    return resp


@api_view(["GET"])
@permission_classes([AllowAny])
def remember_device_prefill(request):
    """Read the remember-device cookie and return the associated username."""
    raw_token = request.COOKIES.get(REMEMBER_COOKIE_NAME)
    if not raw_token:
        return Response({"username": None})

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    workstation_id = request.headers.get("X-Workstation-ID", "")
    try:
        lookup = {"token_hash": token_hash, "expires_at__gt": timezone.now()}
        # Validate against the originating workstation to prevent cookie reuse
        if workstation_id:
            lookup["workstation_id"] = workstation_id
        device = RememberDevice.objects.get(**lookup)
        return Response({"username": device.username})
    except RememberDevice.DoesNotExist:
        return Response({"username": None})


# ---------------------------------------------------------------------------
# Guest profiles
# ---------------------------------------------------------------------------

MAX_GUEST_PROFILES_PER_SESSION = 5


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def guest_profile_list(request):
    """List or create guest profiles for the current session."""
    session_key = request.session.session_key

    if request.method == "GET":
        profiles = GuestProfile.objects.filter(
            session_key=session_key, user=request.user,
        ).order_by("-created_at")
        serializer = GuestProfileSerializer(profiles, many=True)
        return Response(serializer.data)

    # POST - create a new guest profile
    existing_count = GuestProfile.objects.filter(
        session_key=session_key, user=request.user,
    ).count()
    if existing_count >= MAX_GUEST_PROFILES_PER_SESSION:
        return Response(
            {
                "error": "max_profiles_reached",
                "message": f"Maximum of {MAX_GUEST_PROFILES_PER_SESSION} guest profiles per session.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = GuestProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    profile = serializer.save(session_key=session_key, user=request.user)

    request._audit_context = {
        "event_type": "create",
        "target_model": "GuestProfile",
        "target_id": str(profile.pk),
        "target_repr": f"Guest profile '{profile.display_name}' created by {request.user.username}",
    }

    return Response(
        GuestProfileSerializer(profile).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def guest_profile_activate(request, pk):
    """Set a guest profile as active for the current session (deactivates all others)."""
    session_key = request.session.session_key

    try:
        profile = GuestProfile.objects.get(
            pk=pk, session_key=session_key, user=request.user,
        )
    except GuestProfile.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Guest profile not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Deactivate all profiles for this session, then activate the selected one
    GuestProfile.objects.filter(
        session_key=session_key, user=request.user,
    ).update(is_active=False)

    profile.is_active = True
    profile.save(update_fields=["is_active"])

    request._audit_context = {
        "event_type": "update",
        "target_model": "GuestProfile",
        "target_id": str(profile.pk),
        "target_repr": f"Guest profile '{profile.display_name}' activated by {request.user.username}",
    }

    return Response(GuestProfileSerializer(profile).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def guest_recent_patients(request, pk):
    """
    GET  -- List recent patients for a guest profile.
    POST -- Record a patient access for a guest profile.
           Expects: { "patient_id": "<uuid>" }
    """
    session_key = request.session.session_key

    try:
        profile = GuestProfile.objects.get(
            pk=pk, session_key=session_key, user=request.user,
        )
    except GuestProfile.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Guest profile not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "POST":
        patient_id = request.data.get("patient_id")
        if not patient_id:
            return Response(
                {
                    "error": "validation_error",
                    "message": "The 'patient_id' field is required.",
                    "status_code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create or update (touch accessed_at) the recent patient record
        recent, created = GuestRecentPatient.objects.update_or_create(
            guest_profile=profile,
            patient_id=patient_id,
            defaults={},  # accessed_at uses auto_now so it updates on save
        )
        if not created:
            # Force accessed_at update for existing records
            recent.save()

        serializer = GuestRecentPatientSerializer(recent)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # GET
    patients = GuestRecentPatient.objects.filter(guest_profile=profile)
    serializer = GuestRecentPatientSerializer(patients, many=True)
    return Response(serializer.data)
