"""DRF serializers for the accounts app."""
from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import (
    GuestProfile,
    GuestRecentPatient,
    LoginAttempt,
    RememberDevice,
    SudoToken,
    User,
    WorkstationBlacklist,
)


# ---------------------------------------------------------------------------
# Auth serializers
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    remember_device = serializers.BooleanField(required=False, default=False)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        # Run Django's built-in password validators
        password_validation.validate_password(value, self.context.get("user"))
        return value


class UserInfoSerializer(serializers.ModelSerializer):
    """Read-only user info returned after login and in session endpoints."""

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "role", "is_active", "date_joined"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# User management serializers
# ---------------------------------------------------------------------------

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "role", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "email", "role"]


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "role", "is_active", "date_joined"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Guest-profile serializers
# ---------------------------------------------------------------------------

class GuestProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestProfile
        fields = ["id", "display_name", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]


class GuestRecentPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestRecentPatient
        fields = ["id", "patient_id", "accessed_at"]
        read_only_fields = ["id", "accessed_at"]


# ---------------------------------------------------------------------------
# Workstation serializers
# ---------------------------------------------------------------------------

class WorkstationBlacklistSerializer(serializers.ModelSerializer):
    released_by_username = serializers.CharField(
        source="released_by.username", read_only=True, default=None,
    )

    class Meta:
        model = WorkstationBlacklist
        fields = [
            "id", "client_ip", "workstation_id", "lockout_count",
            "first_lockout_at", "blacklisted_at", "is_active",
            "released_by_username", "released_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Sudo serializers
# ---------------------------------------------------------------------------

class SudoAcquireSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    action_class = serializers.ChoiceField(
        choices=[c[0] for c in SudoToken.ACTION_CLASSES],
    )


class SudoStatusSerializer(serializers.Serializer):
    action_class = serializers.CharField()
    expires_at = serializers.FloatField()
