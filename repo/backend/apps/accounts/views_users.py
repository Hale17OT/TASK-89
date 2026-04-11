"""User management views: CRUD for admin-managed user accounts."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User
from .permissions import IsAdmin, SudoRequired
from .serializers import UserCreateSerializer, UserInfoSerializer, UserListSerializer, UserUpdateSerializer

logger = logging.getLogger("medrights.auth")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_list(request):
    """
    GET:  Paginated list of all users.
    POST: Create a new user account.
    """
    if request.method == "GET":
        queryset = User.objects.all().order_by("-date_joined")

        # Simple search filter
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(username__icontains=search)

        role_filter = request.query_params.get("role")
        if role_filter:
            queryset = queryset.filter(role=role_filter)

        is_active_filter = request.query_params.get("is_active")
        if is_active_filter is not None:
            queryset = queryset.filter(is_active=is_active_filter.lower() == "true")

        # Manual pagination (DRF function-based views don't auto-paginate)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)  # cap
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()

        users = queryset[start:end]
        serializer = UserListSerializer(users, many=True)

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        })

    # POST - create user
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    logger.info(
        "User created",
        extra={
            "created_by": request.user.username,
            "new_user": user.username,
            "role": user.role,
        },
    )

    request._audit_context = {
        "event_type": "user_create",
        "target_model": "User",
        "target_id": str(user.pk),
        "target_repr": user.username,
        "extra_data": {"role": user.role},
    }

    return Response(
        UserInfoSerializer(user).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_detail(request, pk):
    """
    GET:   Retrieve a single user.
    PATCH: Update mutable fields (full_name, email, role).
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "User not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(UserInfoSerializer(user).data)

    # PATCH
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)

    old_values = {
        field: getattr(user, field)
        for field in serializer.validated_data
    }

    serializer.save()

    field_changes = {
        field: {"old": str(old_values[field]), "new": str(getattr(user, field))}
        for field in serializer.validated_data
        if str(old_values[field]) != str(getattr(user, field))
    }

    request._audit_context = {
        "event_type": "user_update",
        "target_model": "User",
        "target_id": str(user.pk),
        "target_repr": user.username,
        "field_changes": field_changes,
    }

    return Response(UserInfoSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_disable(request, pk):
    """
    Disable a user account. Requires sudo mode (action_class=user_disable).
    """
    # Check sudo requirement manually since @api_view + SudoRequired
    # needs the action class to be known
    if "user_disable" not in getattr(request, "sudo_actions", set()):
        return Response(
            {
                "error": "sudo_required",
                "message": "Sudo mode required. Please re-authenticate to perform this action.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if not request.data.get("confirm"):
        return Response(
            {
                "error": "confirmation_required",
                "message": "Set confirm=true to proceed.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "User not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if user.pk == request.user.pk:
        return Response(
            {
                "error": "self_disable",
                "message": "You cannot disable your own account.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        return Response(
            {
                "error": "already_disabled",
                "message": "User is already disabled.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = False
    user.save(update_fields=["is_active"])

    logger.info(
        "User disabled",
        extra={
            "disabled_by": request.user.username,
            "disabled_user": user.username,
        },
    )

    request._audit_context = {
        "event_type": "user_disable",
        "target_model": "User",
        "target_id": str(user.pk),
        "target_repr": user.username,
    }

    return Response({
        "message": f"User '{user.username}' has been disabled.",
        "user": UserInfoSerializer(user).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_enable(request, pk):
    """Re-enable a previously disabled user account."""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "User not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if user.is_active:
        return Response(
            {
                "error": "already_active",
                "message": "User is already active.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = True
    user.save(update_fields=["is_active"])

    logger.info(
        "User re-enabled",
        extra={
            "enabled_by": request.user.username,
            "enabled_user": user.username,
        },
    )

    request._audit_context = {
        "event_type": "user_enable",
        "target_model": "User",
        "target_id": str(user.pk),
        "target_repr": user.username,
    }

    return Response({
        "message": f"User '{user.username}' has been re-enabled.",
        "user": UserInfoSerializer(user).data,
    })
