"""Audit serializers: read-only entry output and filter input."""
from rest_framework import serializers

from .models import AuditEntry


class AuditEntrySerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""

    class Meta:
        model = AuditEntry
        fields = [
            "id",
            "entry_hash",
            "previous_hash",
            "event_type",
            "user",
            "username_snapshot",
            "client_ip",
            "workstation_id",
            "target_model",
            "target_id",
            "target_repr",
            "field_changes",
            "extra_data",
            "created_at",
        ]
        read_only_fields = fields


class AuditEntryFilterSerializer(serializers.Serializer):
    """Input serializer for audit log filtering parameters."""

    event_type = serializers.CharField(required=False, allow_blank=True)
    user_id = serializers.UUIDField(required=False)
    target_model = serializers.CharField(required=False, allow_blank=True)
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)
