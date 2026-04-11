"""Initial migration for media_engine app."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mpi", "0001_initial"),
        ("consent", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("original_file", models.CharField(max_length=500)),
                ("watermarked_file", models.CharField(blank=True, default="", max_length=500)),
                ("original_filename", models.CharField(max_length=255)),
                ("mime_type", models.CharField(max_length=100)),
                ("file_size_bytes", models.BigIntegerField()),
                ("pixel_hash", models.CharField(db_index=True, max_length=64)),
                ("file_hash", models.CharField(max_length=64)),
                ("originality_status", models.CharField(choices=[("original", "Original"), ("reposted", "Reposted"), ("disputed", "Disputed")], db_index=True, default="original", max_length=20)),
                ("watermark_settings", models.JSONField(blank=True, null=True)),
                ("watermark_burned", models.BooleanField(default=False)),
                ("evidence_metadata", models.JSONField(default=dict)),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="media_assets", to="consent.consent")),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="media_assets", to="mpi.patient")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_media", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "media_assets",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Citation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("citation_text", models.TextField()),
                ("authorization_file_path", models.CharField(blank=True, max_length=500, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_citations", to=settings.AUTH_USER_MODEL)),
                ("media_asset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="citations", to="media_engine.mediaasset")),
            ],
            options={
                "db_table": "media_citations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MediaDerivative",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("derivative_path", models.CharField(max_length=500)),
                ("derivative_hash", models.CharField(max_length=64)),
                ("watermark_applied", models.BooleanField(default=False)),
                ("watermark_settings", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_derivatives", to=settings.AUTH_USER_MODEL)),
                ("parent_asset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="derivatives", to="media_engine.mediaasset")),
            ],
            options={
                "db_table": "media_derivatives",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="InfringementReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("screenshot_path", models.CharField(blank=True, max_length=500, null=True)),
                ("reference_url", models.URLField(blank=True, max_length=2048, null=True)),
                ("notes", models.TextField()),
                ("status", models.CharField(choices=[("open", "Open"), ("investigating", "Investigating"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], db_index=True, default="open", max_length=20)),
                ("resolution_notes", models.TextField(blank=True, default="")),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("investigating_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("dismissed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_infringements", to=settings.AUTH_USER_MODEL)),
                ("media_asset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="infringement_reports", to="media_engine.mediaasset")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reported_infringements", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "infringement_reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DisputeHistory",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("old_status", models.CharField(max_length=20)),
                ("new_status", models.CharField(max_length=20)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("changed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dispute_changes", to=settings.AUTH_USER_MODEL)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dispute_history", to="media_engine.infringementreport")),
            ],
            options={
                "db_table": "dispute_history",
                "ordering": ["-changed_at"],
            },
        ),
    ]
