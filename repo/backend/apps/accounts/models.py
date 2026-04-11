"""Accounts models: User, Workstation, LoginAttempt, Lockout, GuestProfile, etc."""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access."""

    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("front_desk", "Front Desk Staff"),
        ("clinician", "Clinician"),
        ("compliance", "Compliance Officer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="front_desk")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_password_change = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.username} ({self.role})"


class WorkstationBlacklist(models.Model):
    """Tracks blacklisted workstations (IP + workstation ID combo)."""

    id = models.BigAutoField(primary_key=True)
    client_ip = models.GenericIPAddressField()
    workstation_id = models.CharField(max_length=100)
    lockout_count = models.PositiveIntegerField(default=1)
    first_lockout_at = models.DateTimeField(auto_now_add=True)
    blacklisted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="unblocked_workstations",
    )
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workstation_blacklist"
        unique_together = ("client_ip", "workstation_id")


class LoginAttempt(models.Model):
    """Records every login attempt for throttling."""

    id = models.BigAutoField(primary_key=True)
    username_tried = models.CharField(max_length=150)
    client_ip = models.GenericIPAddressField()
    workstation_id = models.CharField(max_length=100, default="")
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    was_successful = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "login_attempts"
        indexes = [
            models.Index(fields=["client_ip", "workstation_id", "attempted_at"]),
        ]


class Lockout(models.Model):
    """Records lockout events for blacklist threshold tracking."""

    id = models.BigAutoField(primary_key=True)
    client_ip = models.GenericIPAddressField()
    workstation_id = models.CharField(max_length=100)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    unlocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lockouts"


class GuestProfile(models.Model):
    """UI-level guest profile within a single authenticated session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guest_profiles",
    )
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "guest_profiles"


class GuestRecentPatient(models.Model):
    """Recent-patient list scoped to a guest profile."""

    id = models.BigAutoField(primary_key=True)
    guest_profile = models.ForeignKey(
        GuestProfile, on_delete=models.CASCADE, related_name="recent_patients",
    )
    patient_id = models.UUIDField()  # FK enforced at app level, not DB (avoids circular)
    accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guest_profile_patients"
        unique_together = ("guest_profile", "patient_id")
        ordering = ["-accessed_at"]


class RememberDevice(models.Model):
    """30-day device cookie for username pre-fill."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    workstation_id = models.CharField(max_length=100)
    username = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "device_tokens"


class SudoToken(models.Model):
    """5-minute scoped privilege elevation token."""

    ACTION_CLASSES = [
        ("user_disable", "Disable User Account"),
        ("bulk_export", "Bulk Data Export"),
        ("log_purge", "Audit Log Purge"),
        ("workstation_unblock", "Workstation Unblock"),
        ("system_config", "System Configuration"),
        ("policy_update", "Policy Update"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    action_class = models.CharField(max_length=50, choices=ACTION_CLASSES)
    token_hash = models.CharField(max_length=64, unique=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sudo_tokens"


class SystemPolicy(models.Model):
    """Configurable system-wide policy parameters managed by administrators."""

    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="updated_policies",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_policies"

    def __str__(self):
        return f"{self.key}={self.value}"
