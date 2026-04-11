"""Policy management views: list and update system-wide policies."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SystemPolicy
from .permissions import IsAdmin

logger = logging.getLogger("medrights.auth")


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def policy_list(request):
    """
    GET /api/v1/policies/

    List all system policies. Admin only.
    """
    policies = SystemPolicy.objects.all().order_by("key")
    data = [
        {
            "key": p.key,
            "value": p.value,
            "description": p.description,
            "updated_by": str(p.updated_by_id) if p.updated_by_id else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in policies
    ]
    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsAdmin])
def policy_update(request, key):
    """
    PATCH /api/v1/policies/{key}/

    Update a single policy value. Admin only.
    Requires sudo mode (action_class=policy_update) and confirm=true.
    """
    if "policy_update" not in getattr(request, "sudo_actions", set()):
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
        policy = SystemPolicy.objects.get(key=key)
    except SystemPolicy.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": f"Policy '{key}' not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    new_value = request.data.get("value")
    if new_value is None:
        return Response(
            {
                "error": "validation_error",
                "message": "The 'value' field is required.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_value = policy.value
    policy.value = new_value
    policy.updated_by = request.user
    policy.save(update_fields=["value", "updated_by", "updated_at"])

    logger.info(
        "Policy updated",
        extra={
            "updated_by": request.user.username,
            "policy_key": key,
            "old_value": str(old_value),
            "new_value": str(new_value),
        },
    )

    request._audit_context = {
        "event_type": "policy_update",
        "target_model": "SystemPolicy",
        "target_id": key,
        "target_repr": f"Policy '{key}' updated",
        "field_changes": {"value": {"old": str(old_value), "new": str(new_value)}},
    }

    return Response({
        "key": policy.key,
        "value": policy.value,
        "description": policy.description,
        "updated_by": str(policy.updated_by_id) if policy.updated_by_id else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    })
