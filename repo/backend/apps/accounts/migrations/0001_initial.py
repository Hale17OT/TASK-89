"""Initial migration for accounts app."""
import uuid

import django.contrib.auth.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, verbose_name="superuser status")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("username", models.CharField(db_index=True, max_length=150, unique=True)),
                ("full_name", models.CharField(blank=True, max_length=255)),
                ("email", models.CharField(blank=True, max_length=255)),
                ("role", models.CharField(choices=[("admin", "Administrator"), ("front_desk", "Front Desk Staff"), ("clinician", "Clinician"), ("compliance", "Compliance Officer")], default="front_desk", max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(auto_now_add=True)),
                ("last_password_change", models.DateTimeField(auto_now_add=True)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "db_table": "users",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="WorkstationBlacklist",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("client_ip", models.GenericIPAddressField()),
                ("workstation_id", models.CharField(max_length=100)),
                ("lockout_count", models.PositiveIntegerField(default=1)),
                ("first_lockout_at", models.DateTimeField(auto_now_add=True)),
                ("blacklisted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("released_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="unblocked_workstations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "workstation_blacklist",
                "unique_together": {("client_ip", "workstation_id")},
            },
        ),
        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username_tried", models.CharField(max_length=150)),
                ("client_ip", models.GenericIPAddressField()),
                ("workstation_id", models.CharField(default="", max_length=100)),
                ("attempted_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("was_successful", models.BooleanField(default=False)),
                ("failure_reason", models.CharField(blank=True, max_length=100)),
            ],
            options={
                "db_table": "login_attempts",
            },
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(fields=["client_ip", "workstation_id", "attempted_at"], name="login_attem_client__idx"),
        ),
        migrations.CreateModel(
            name="Lockout",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("client_ip", models.GenericIPAddressField()),
                ("workstation_id", models.CharField(max_length=100)),
                ("locked_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("unlocked_at", models.DateTimeField(blank=True, null=True)),
                ("unlocked_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "lockouts",
            },
        ),
        migrations.CreateModel(
            name="GuestProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("session_key", models.CharField(db_index=True, max_length=40)),
                ("display_name", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guest_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "guest_profiles",
            },
        ),
        migrations.CreateModel(
            name="GuestRecentPatient",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("patient_id", models.UUIDField()),
                ("accessed_at", models.DateTimeField(auto_now=True)),
                ("guest_profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recent_patients", to="accounts.guestprofile")),
            ],
            options={
                "db_table": "guest_profile_patients",
                "ordering": ["-accessed_at"],
                "unique_together": {("guest_profile", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="RememberDevice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token_hash", models.CharField(db_index=True, max_length=128, unique=True)),
                ("workstation_id", models.CharField(max_length=100)),
                ("username", models.CharField(max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
            options={
                "db_table": "device_tokens",
            },
        ),
        migrations.CreateModel(
            name="SudoToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("session_key", models.CharField(max_length=40)),
                ("action_class", models.CharField(choices=[("user_disable", "Disable User Account"), ("bulk_export", "Bulk Data Export"), ("log_purge", "Audit Log Purge"), ("workstation_unblock", "Workstation Unblock"), ("system_config", "System Configuration")], max_length=50)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("granted_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(default=False)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "sudo_tokens",
            },
        ),
    ]
