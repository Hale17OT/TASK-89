"""Initial migration for audit app."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEntry",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("entry_hash", models.CharField(db_index=True, max_length=64)),
                ("previous_hash", models.CharField(max_length=64)),
                ("event_type", models.CharField(choices=[("login_success", "Login Success"), ("login_failure", "Login Failure"), ("logout", "Logout"), ("session_timeout", "Session Timeout"), ("create", "Create"), ("update", "Update"), ("key_field_change", "Key Field Change"), ("export", "Export"), ("consent_granted", "Consent Granted"), ("consent_revoked", "Consent Revoked"), ("break_glass", "Break Glass"), ("break_glass_review", "Break Glass Review"), ("approval", "Approval"), ("media_upload", "Media Upload"), ("media_dispute", "Media Dispute"), ("infringement_report", "Infringement Report"), ("payment_posted", "Payment Posted"), ("refund_processed", "Refund Processed"), ("sudo_mode_enter", "Sudo Mode Enter"), ("sudo_mode_action", "Sudo Mode Action"), ("user_disabled", "User Disabled"), ("workstation_blacklisted", "Workstation Blacklisted"), ("workstation_unblocked", "Workstation Unblocked"), ("bulk_export", "Bulk Export"), ("log_purge", "Log Purge"), ("report_generated", "Report Generated"), ("report_delivered", "Report Delivered"), ("password_change", "Password Change")], db_index=True, max_length=50)),
                ("username_snapshot", models.CharField(max_length=150)),
                ("client_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("workstation_id", models.CharField(blank=True, default="", max_length=100)),
                ("target_model", models.CharField(blank=True, default="", max_length=100)),
                ("target_id", models.CharField(blank=True, default="", max_length=64)),
                ("target_repr", models.CharField(blank=True, default="", max_length=255)),
                ("field_changes", models.JSONField(blank=True, default=dict)),
                ("extra_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "audit_log",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditentry",
            index=models.Index(fields=["event_type", "created_at"], name="audit_log_event_t_idx"),
        ),
        migrations.AddIndex(
            model_name="auditentry",
            index=models.Index(fields=["user", "created_at"], name="audit_log_user_id_idx"),
        ),
        migrations.AddIndex(
            model_name="auditentry",
            index=models.Index(fields=["target_model", "target_id"], name="audit_log_target__idx"),
        ),
    ]
