"""Workstation management views: list blacklisted workstations, unblock."""
import logging

from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import WorkstationBlacklist
from .permissions import IsAdmin
from .serializers import WorkstationBlacklistSerializer

logger = logging.getLogger("medrights.auth")


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def workstation_list(request):
    """List all blacklisted workstations (active and historical)."""
    active_only = request.query_params.get("active_only", "true").lower() == "true"

    queryset = WorkstationBlacklist.objects.all().order_by("-blacklisted_at")
    if active_only:
        queryset = queryset.filter(is_active=True)

    serializer = WorkstationBlacklistSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def workstation_unblock(request, pk):
    """
    Remove a workstation from the blacklist. Requires sudo mode
    (action_class=workstation_unblock).
    """
    # Check sudo requirement
    if "workstation_unblock" not in getattr(request, "sudo_actions", set()):
        return Response(
            {
                "error": "sudo_required",
                "message": "Sudo mode required. Please re-authenticate to perform this action.",
                "status_code": 403,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        entry = WorkstationBlacklist.objects.get(pk=pk)
    except WorkstationBlacklist.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Workstation blacklist entry not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if not entry.is_active:
        return Response(
            {
                "error": "already_unblocked",
                "message": "This workstation is not currently blacklisted.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    entry.is_active = False
    entry.released_by = request.user
    entry.released_at = timezone.now()
    entry.save(update_fields=["is_active", "released_by", "released_at"])

    logger.info(
        "Workstation unblocked",
        extra={
            "unblocked_by": request.user.username,
            "client_ip": entry.client_ip,
            "workstation_id": entry.workstation_id,
        },
    )

    request._audit_context = {
        "event_type": "workstation_unblock",
        "target_model": "WorkstationBlacklist",
        "target_id": str(entry.pk),
        "target_repr": f"{entry.client_ip}/{entry.workstation_id}",
    }

    return Response({
        "message": "Workstation has been unblocked.",
        "workstation": WorkstationBlacklistSerializer(entry).data,
    })
