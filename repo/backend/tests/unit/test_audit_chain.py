"""Unit tests for the tamper-evident audit hash chain."""
import pytest

from apps.audit.models import GENESIS_HASH, AuditEntry
from apps.audit.service import create_audit_entry, verify_audit_chain


pytestmark = pytest.mark.django_db


class TestAuditChain:

    def test_create_audit_entry_genesis(self):
        """The very first audit entry should reference the 64-zero sentinel."""
        entry = create_audit_entry(
            event_type="create",
            username_snapshot="test_user",
            target_model="Patient",
            target_id="abc-123",
            target_repr="Patient MRN-001",
        )
        assert entry.previous_hash == GENESIS_HASH
        assert len(entry.entry_hash) == 64
        assert entry.entry_hash != GENESIS_HASH

    def test_create_audit_entry_chain(self):
        """The second entry must reference the first entry's hash."""
        first = create_audit_entry(
            event_type="create",
            username_snapshot="user_a",
            target_model="Patient",
            target_id="1",
        )
        second = create_audit_entry(
            event_type="update",
            username_snapshot="user_b",
            target_model="Patient",
            target_id="1",
        )
        assert second.previous_hash == first.entry_hash

    def test_verify_chain_valid(self):
        """Create 5 entries and confirm the chain verifies cleanly."""
        for i in range(5):
            create_audit_entry(
                event_type="create",
                username_snapshot=f"user_{i}",
                target_model="TestModel",
                target_id=str(i),
            )

        is_valid, broken_at, total = verify_audit_chain()
        assert is_valid is True
        assert broken_at is None
        assert total == 5

    def test_verify_chain_tampered(self):
        """Tamper with a middle entry's hash and confirm detection."""
        for i in range(5):
            create_audit_entry(
                event_type="create",
                username_snapshot=f"user_{i}",
                target_model="TestModel",
                target_id=str(i),
            )

        # Tamper with the 3rd entry's entry_hash directly in the DB.
        # The verifier recomputes entry_hash from the entry data and
        # previous_hash.  Changing the stored entry_hash means that the
        # recomputed hash will not match, so the break is detected at
        # the tampered entry itself.
        entries = list(AuditEntry.objects.order_by("id"))
        tampered = entries[2]
        AuditEntry.objects.filter(pk=tampered.pk).update(
            entry_hash="deadbeef" * 8,
        )

        is_valid, broken_at, total = verify_audit_chain()
        assert is_valid is False
        assert broken_at is not None
        # The chain break is detected at the tampered entry (recomputed
        # hash mismatch) or at the next entry (previous_hash mismatch).
        assert broken_at in (tampered.pk, entries[3].pk)

    def test_verify_chain_empty(self):
        """An empty chain is trivially valid."""
        is_valid, broken_at, total = verify_audit_chain()
        assert is_valid is True
        assert broken_at is None
        assert total == 0
