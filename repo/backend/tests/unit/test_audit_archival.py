"""Unit tests for audit entry archival task."""
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.audit.models import AuditArchiveSegment, AuditEntry


pytestmark = pytest.mark.django_db


def _create_entry(days_ago=0, **overrides):
    """Helper: create an audit entry with a specific age."""
    from apps.audit.service import create_audit_entry
    entry = create_audit_entry(
        event_type=overrides.get("event_type", "test_event"),
        user=None,
        username_snapshot="test",
        client_ip="127.0.0.1",
        workstation_id="ws-test",
        target_model="Test",
        target_id="1",
        target_repr="test",
    )
    if days_ago:
        old_date = timezone.now() - timedelta(days=days_ago)
        AuditEntry.objects.filter(pk=entry.pk).update(created_at=old_date)
        entry.refresh_from_db()
    return entry


class TestArchiveOldEntries:
    def test_no_old_entries_is_noop(self):
        """When all entries are recent, nothing is archived."""
        _create_entry(days_ago=10)
        from apps.audit.tasks import archive_old_entries
        archive_old_entries()
        assert AuditEntry.objects.filter(is_archived=True).count() == 0

    def test_old_entries_are_archived(self, tmp_path):
        """Entries older than 180 days are marked as archived."""
        recent = _create_entry(days_ago=10)
        old1 = _create_entry(days_ago=200)
        old2 = _create_entry(days_ago=250)

        with override_settings(MEDRIGHTS_STORAGE_ROOT=str(tmp_path)):
            from apps.audit.tasks import archive_old_entries
            archive_old_entries()

        # Old entries marked archived
        old1.refresh_from_db()
        old2.refresh_from_db()
        recent.refresh_from_db()
        assert old1.is_archived is True
        assert old2.is_archived is True
        assert recent.is_archived is False

    def test_archive_creates_segment_record(self, tmp_path):
        """Archival creates an AuditArchiveSegment boundary record."""
        _create_entry(days_ago=200)

        with override_settings(MEDRIGHTS_STORAGE_ROOT=str(tmp_path)):
            from apps.audit.tasks import archive_old_entries
            archive_old_entries()

        segments = AuditArchiveSegment.objects.all()
        assert segments.count() == 1
        segment = segments.first()
        assert segment.entries_count == 1
        assert segment.segment_end_hash != ""

    def test_archive_writes_jsonl_file(self, tmp_path):
        """Archival writes entries to a JSONL file on disk."""
        _create_entry(days_ago=200)

        with override_settings(MEDRIGHTS_STORAGE_ROOT=str(tmp_path)):
            from apps.audit.tasks import archive_old_entries
            archive_old_entries()

        archive_dir = tmp_path / "audit_archive"
        assert archive_dir.exists()
        jsonl_files = list(archive_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        content = jsonl_files[0].read_text()
        assert '"event_type": "test_event"' in content

    def test_idempotent_rerun(self, tmp_path):
        """Running archival twice does not re-archive already-archived entries."""
        _create_entry(days_ago=200)

        with override_settings(MEDRIGHTS_STORAGE_ROOT=str(tmp_path)):
            from apps.audit.tasks import archive_old_entries
            archive_old_entries()
            archive_old_entries()

        assert AuditArchiveSegment.objects.count() == 1
        assert AuditEntry.objects.filter(is_archived=True).count() == 1
