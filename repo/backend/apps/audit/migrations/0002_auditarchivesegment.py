"""Add AuditArchiveSegment model for chain-safe audit purging."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditArchiveSegment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "segment_end_entry_id",
                    models.BigIntegerField(
                        help_text="ID of the last audit entry in this archived segment."
                    ),
                ),
                (
                    "segment_end_hash",
                    models.CharField(
                        help_text="entry_hash of the last entry in the archived segment.",
                        max_length=64,
                    ),
                ),
                (
                    "archive_file",
                    models.CharField(
                        help_text="Relative path to the JSONL archive file.",
                        max_length=500,
                    ),
                ),
                ("entries_count", models.IntegerField(default=0)),
                ("before_date", models.DateTimeField()),
                ("purged_at", models.DateTimeField(auto_now_add=True)),
                (
                    "purged_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "audit_archive_segments",
                "ordering": ["-purged_at"],
            },
        ),
    ]
