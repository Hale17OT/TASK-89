"""Celery tasks for the accounts app."""
import logging

from celery import shared_task
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger("medrights")


@shared_task(name="apps.accounts.tasks.cleanup_expired_sessions")
def cleanup_expired_sessions():
    """
    Delete expired Django sessions and clean up orphaned guest profiles
    whose session no longer exists.
    """
    now = timezone.now()

    # 1. Delete expired sessions from the database
    expired_count, _ = Session.objects.filter(expire_date__lt=now).delete()
    if expired_count:
        logger.info("Deleted %d expired sessions", expired_count)

    # 2. Clean up guest profiles whose session_key no longer exists
    from apps.accounts.models import GuestProfile

    active_session_keys = set(
        Session.objects.values_list("session_key", flat=True)
    )
    orphaned_profiles = GuestProfile.objects.exclude(
        session_key__in=active_session_keys
    )
    orphan_count, _ = orphaned_profiles.delete()
    if orphan_count:
        logger.info("Deleted %d orphaned guest profiles", orphan_count)

    return {
        "expired_sessions_deleted": expired_count,
        "orphaned_profiles_deleted": orphan_count,
    }
