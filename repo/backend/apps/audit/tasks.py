"""Audit Celery tasks: partition maintenance and archival for the audit_log table."""
import json
import logging
import os
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import connection
from django.utils import timezone

logger = logging.getLogger("medrights.audit")


@shared_task(name="apps.audit.tasks.maintain_partitions")
def maintain_partitions():
    """
    Maintain date-based partitions on the audit_log table.

    Runs monthly via Celery Beat. On MySQL, inspects the current
    partition layout and logs the state for operational visibility.
    On non-MySQL backends (e.g., SQLite in tests), this is a no-op.
    """
    engine = connection.vendor
    if engine != "mysql":
        logger.info(
            "Partition maintenance skipped: backend is %s (requires MySQL)",
            engine,
        )
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT PARTITION_NAME FROM INFORMATION_SCHEMA.PARTITIONS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'audit_log' "
                "ORDER BY PARTITION_ORDINAL_POSITION"
            )
            partitions = [row[0] for row in cursor.fetchall() if row[0]]

            if not partitions:
                logger.info("audit_log has no partitions configured; skipping")
                return

            logger.info(
                "Partition maintenance: %d partitions on audit_log: %s",
                len(partitions),
                ", ".join(partitions[:5]) + ("..." if len(partitions) > 5 else ""),
            )
    except Exception:
        logger.exception("Partition maintenance failed")


@shared_task(name="apps.audit.tasks.archive_old_entries")
def archive_old_entries():
    """Archive audit entries older than 180 days to local storage."""
    from .models import AuditArchiveSegment, AuditEntry

    cutoff = timezone.now() - timedelta(days=180)

    entries_qs = (
        AuditEntry.objects.filter(created_at__lt=cutoff, is_archived=False)
        .order_by("id")
    )
    count = entries_qs.count()

    if count == 0:
        logger.info("No audit entries older than 180 days to archive.")
        return

    storage_root = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", "storage")
    archive_dir = os.path.join(storage_root, "audit_archive")
    os.makedirs(archive_dir, exist_ok=True)

    archive_filename = f"archive_{cutoff.date().isoformat()}.jsonl"
    archive_relative = os.path.join("audit_archive", archive_filename)
    archive_absolute = os.path.join(storage_root, archive_relative)

    last_entry = None
    archived_ids = []

    with open(archive_absolute, "w", encoding="utf-8") as f:
        for entry in entries_qs.iterator(chunk_size=1000):
            record = {
                "id": entry.pk,
                "entry_hash": entry.entry_hash,
                "previous_hash": entry.previous_hash,
                "event_type": entry.event_type,
                "user_id": str(entry.user_id) if entry.user_id else None,
                "username_snapshot": entry.username_snapshot,
                "client_ip": str(entry.client_ip) if entry.client_ip else "",
                "workstation_id": entry.workstation_id,
                "target_model": entry.target_model,
                "target_id": entry.target_id,
                "target_repr": entry.target_repr,
                "field_changes": entry.field_changes,
                "extra_data": entry.extra_data,
                "created_at": entry.created_at.isoformat(),
            }
            f.write(json.dumps(record, default=str) + "\n")
            archived_ids.append(entry.pk)
            last_entry = entry

    if last_entry is None:
        logger.info("No entries were written during archival.")
        return

    # Record the segment boundary hash
    AuditArchiveSegment.objects.create(
        segment_end_entry_id=last_entry.pk,
        segment_end_hash=last_entry.entry_hash,
        archive_file=archive_relative,
        entries_count=len(archived_ids),
        before_date=cutoff,
    )

    # Mark entries as archived (safer than deleting)
    AuditEntry.objects.filter(pk__in=archived_ids).update(is_archived=True)

    logger.info(
        "Archived %d audit entries older than %s to %s",
        len(archived_ids),
        cutoff.date().isoformat(),
        archive_relative,
    )
