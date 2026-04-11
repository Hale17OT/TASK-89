"""Initial migration for reports app."""
import uuid

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
            name="ReportSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("report_type", models.CharField(choices=[("daily_reconciliation", "Daily Reconciliation"), ("consent_expiry", "Consent Expiry"), ("break_glass_review", "Break Glass Review"), ("media_originality", "Media Originality"), ("financial_summary", "Financial Summary"), ("audit_activity", "Audit Activity")], max_length=100)),
                ("schedule", models.CharField(choices=[("daily", "Daily"), ("weekly", "Weekly")], max_length=20)),
                ("output_format", models.CharField(choices=[("pdf", "PDF"), ("excel", "Excel"), ("image", "Image")], max_length=10)),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("run_time", models.TimeField(default="23:59:00")),
                ("run_day_of_week", models.IntegerField(blank=True, help_text="0=Monday .. 6=Sunday. Null for daily schedules.", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="report_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "report_subscriptions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OutboxItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("report_name", models.CharField(max_length=300)),
                ("file_path", models.CharField(blank=True, default="", max_length=500)),
                ("file_format", models.CharField(choices=[("pdf", "PDF"), ("xlsx", "XLSX"), ("png", "PNG")], max_length=10)),
                ("file_size_bytes", models.BigIntegerField(default=0)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("generating", "Generating"), ("delivered", "Delivered"), ("failed", "Failed"), ("stalled", "Stalled")], db_index=True, default="queued", max_length=20)),
                ("retry_count", models.IntegerField(default=0)),
                ("max_retries", models.IntegerField(default=3)),
                ("last_error", models.TextField(blank=True, default="")),
                ("next_retry_at", models.DateTimeField(blank=True, null=True)),
                ("delivery_target", models.CharField(choices=[("print_queue", "Print Queue"), ("shared_folder", "Shared Folder")], default="shared_folder", max_length=50)),
                ("delivery_target_path", models.CharField(blank=True, default="", max_length=500)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("stalled_at", models.DateTimeField(blank=True, null=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("acknowledged_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="acknowledged_outbox_items", to=settings.AUTH_USER_MODEL)),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="outbox_items", to="reports.reportsubscription")),
            ],
            options={
                "db_table": "outbox_tasks",
                "ordering": ["-generated_at"],
            },
        ),
    ]
