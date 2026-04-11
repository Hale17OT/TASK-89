"""Reports & Outbox serializers."""
from rest_framework import serializers

from .models import (
    OutboxItem,
    OutputFormat,
    ReportSubscription,
    ReportType,
    ScheduleChoice,
)


# ---------------------------------------------------------------------------
# Report Subscriptions
# ---------------------------------------------------------------------------

class ReportSubscriptionCreateSerializer(serializers.ModelSerializer):
    """Validates incoming data for creating a report subscription."""

    class Meta:
        model = ReportSubscription
        fields = [
            "name",
            "report_type",
            "schedule",
            "output_format",
            "parameters",
            "run_time",
            "run_day_of_week",
        ]

    def validate_report_type(self, value):
        if value not in ReportType.values:
            raise serializers.ValidationError(
                f"Invalid report type. Must be one of: {', '.join(ReportType.values)}"
            )
        return value

    def validate_schedule(self, value):
        if value not in ScheduleChoice.values:
            raise serializers.ValidationError(
                f"Invalid schedule. Must be one of: {', '.join(ScheduleChoice.values)}"
            )
        return value

    def validate_output_format(self, value):
        if value not in OutputFormat.values:
            raise serializers.ValidationError(
                f"Invalid format. Must be one of: {', '.join(OutputFormat.values)}"
            )
        return value

    def validate(self, data):
        schedule = data.get("schedule")
        run_day = data.get("run_day_of_week")

        if schedule == ScheduleChoice.WEEKLY and run_day is None:
            raise serializers.ValidationError(
                {"run_day_of_week": "Required for weekly schedules (0=Mon..6=Sun)."}
            )

        if schedule == ScheduleChoice.DAILY and run_day is not None:
            # Silently clear the day for daily schedules.
            data["run_day_of_week"] = None

        if run_day is not None and not (0 <= run_day <= 6):
            raise serializers.ValidationError(
                {"run_day_of_week": "Must be between 0 (Monday) and 6 (Sunday)."}
            )

        return data


class ReportSubscriptionListSerializer(serializers.ModelSerializer):
    """Read-only serializer that exposes all subscription fields."""

    class Meta:
        model = ReportSubscription
        fields = [
            "id",
            "name",
            "report_type",
            "schedule",
            "output_format",
            "parameters",
            "is_active",
            "created_by",
            "run_time",
            "run_day_of_week",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------

class OutboxItemSerializer(serializers.ModelSerializer):
    """Full read-only serializer for outbox items."""

    class Meta:
        model = OutboxItem
        fields = [
            "id",
            "subscription",
            "report_name",
            "file_path",
            "file_format",
            "file_size_bytes",
            "status",
            "retry_count",
            "max_retries",
            "last_error",
            "next_retry_at",
            "delivery_target",
            "delivery_target_path",
            "generated_at",
            "delivered_at",
            "stalled_at",
            "acknowledged_by",
            "acknowledged_at",
        ]
        read_only_fields = fields


class OutboxDashboardSerializer(serializers.Serializer):
    """Computed counts by outbox status for the dashboard view."""

    queued = serializers.IntegerField()
    generating = serializers.IntegerField()
    delivered = serializers.IntegerField()
    failed = serializers.IntegerField()
    stalled = serializers.IntegerField()
    total = serializers.IntegerField()
