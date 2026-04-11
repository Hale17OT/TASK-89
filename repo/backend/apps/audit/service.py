"""
Audit logging service.

Provides hash-chained, tamper-evident audit logging.  Each new entry's
SHA-256 hash is computed from its canonical JSON payload concatenated
with the previous entry's hash, forming a verifiable chain.
"""
import hashlib
import json
import logging

from django.db import transaction

logger = logging.getLogger("medrights.audit")


def _canonical_json(data: dict) -> str:
    """Return a deterministic JSON string for hashing."""
    return json.dumps(data, sort_keys=True, default=str)


def _compute_hash(entry_data: dict, previous_hash: str) -> str:
    """SHA-256( canonical_json(entry_data) + previous_hash )."""
    payload = _canonical_json(entry_data) + previous_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_audit_entry(
    event_type: str,
    user=None,
    username_snapshot: str = "",
    client_ip: str = "",
    workstation_id: str = "",
    target_model: str = "",
    target_id: str = "",
    target_repr: str = "",
    field_changes: dict | None = None,
    extra_data: dict | None = None,
):
    """
    Atomically create a hash-chained audit entry.

    Parameters
    ----------
    event_type : str
        The event type (should match an EventType choice).
    user : User | None
        The Django user who performed the action.
    username_snapshot : str
        Username at the time of the event (survives user renames/deletes).
    client_ip : str
        IP address of the client.
    workstation_id : str
        Workstation identifier from X-Workstation-ID header.
    target_model : str
        The model name of the affected entity.
    target_id : str
        The primary key of the affected entity.
    target_repr : str
        A human-readable representation of the target.
    field_changes : dict | None
        Dict of changed fields: {"field": {"old": ..., "new": ...}}.
    extra_data : dict | None
        Any additional structured data.

    Returns
    -------
    AuditEntry
        The newly created audit entry.
    """
    # Normalize dotted event types to underscore format
    event_type = event_type.replace(".", "_")

    # Lazy import to avoid circular imports at module load time.
    from .models import GENESIS_HASH, AuditEntry

    field_changes = field_changes or {}
    extra_data = extra_data or {}

    # Normalise client_ip: empty strings become None for GenericIPAddressField.
    ip_value = client_ip if client_ip else None

    # Build the data dict used for hashing (excluding computed fields).
    entry_data = {
        "event_type": event_type,
        "user_id": str(user.pk) if user else None,
        "username_snapshot": username_snapshot,
        "client_ip": client_ip,
        "workstation_id": workstation_id,
        "target_model": target_model,
        "target_id": target_id,
        "target_repr": target_repr,
        "field_changes": field_changes,
        "extra_data": extra_data,
    }

    try:
        with transaction.atomic():
            # Lock the last row to prevent concurrent writers from
            # creating entries with the same previous_hash.
            last_entry = (
                AuditEntry.objects
                .select_for_update()
                .order_by("-id")
                .first()
            )

            previous_hash = last_entry.entry_hash if last_entry else GENESIS_HASH
            entry_hash = _compute_hash(entry_data, previous_hash)

            audit_entry = AuditEntry.objects.create(
                entry_hash=entry_hash,
                previous_hash=previous_hash,
                event_type=event_type,
                user=user,
                username_snapshot=username_snapshot,
                client_ip=ip_value,
                workstation_id=workstation_id,
                target_model=target_model,
                target_id=target_id,
                target_repr=target_repr,
                field_changes=field_changes,
                extra_data=extra_data,
            )

        logger.info(
            "AUDIT: %s | %s | %s",
            event_type,
            username_snapshot or "anonymous",
            target_repr,
            extra={"audit_entry": entry_data, "entry_id": audit_entry.pk},
        )

        return audit_entry

    except Exception:
        # Always log even if the DB write fails, so the event is not lost.
        logger.exception(
            "AUDIT WRITE FAILED: %s | %s | %s",
            event_type,
            username_snapshot or "anonymous",
            target_repr,
            extra={"audit_entry": entry_data},
        )
        raise


def verify_audit_chain() -> tuple[bool, int | None, int]:
    """
    Walk the entire audit chain and verify every entry's hash.

    Handles gaps from archived (purged) segments by consulting
    AuditArchiveSegment records.  If the first remaining entry's
    previous_hash matches a known archive segment boundary hash,
    the gap is bridged and verification continues.

    Returns
    -------
    tuple of (is_valid, broken_at_id, total_checked)
        is_valid : bool
            True if the entire chain is intact.
        broken_at_id : int | None
            The ID of the first entry whose hash does not match, or
            None if the chain is valid.
        total_checked : int
            The number of entries inspected.
    """
    from .models import GENESIS_HASH, AuditArchiveSegment, AuditEntry

    # Build a set of known archive boundary hashes for quick lookup
    archive_boundary_hashes = set(
        AuditArchiveSegment.objects.values_list("segment_end_hash", flat=True)
    )

    entries = AuditEntry.objects.order_by("id").iterator(chunk_size=1000)
    expected_previous_hash = GENESIS_HASH
    total_checked = 0

    for entry in entries:
        total_checked += 1

        # Verify previous_hash linkage.
        if entry.previous_hash != expected_previous_hash:
            # Check if the gap is due to an archived segment
            if entry.previous_hash in archive_boundary_hashes:
                # The entry's previous_hash matches a known archive
                # segment boundary, so the chain bridges correctly.
                pass
            elif total_checked == 1 and expected_previous_hash == GENESIS_HASH:
                # First remaining entry after a purge -- check if its
                # previous_hash is a known archive boundary.
                if entry.previous_hash not in archive_boundary_hashes:
                    return False, entry.pk, total_checked
            else:
                return False, entry.pk, total_checked

        # Reconstruct the data dict that was hashed at creation time.
        entry_data = {
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
        }

        recomputed_hash = _compute_hash(entry_data, entry.previous_hash)
        if recomputed_hash != entry.entry_hash:
            return False, entry.pk, total_checked

        expected_previous_hash = entry.entry_hash

    return True, None, total_checked
