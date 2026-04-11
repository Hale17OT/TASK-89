"""Celery tasks for the consent app."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("medrights.consent")


@shared_task(name="apps.consent.tasks.check_expiring_consents")
def check_expiring_consents():
    """
    Find consents expiring within the next 30 days and log them for
    follow-up.  This task is designed to run daily via Celery Beat.

    Returns a summary dict with counts for monitoring.
    """
    from apps.consent.models import Consent

    today = timezone.now().date()
    threshold = today + timedelta(days=30)

    expiring = Consent.objects.filter(
        is_revoked=False,
        expiration_date__isnull=False,
        expiration_date__gte=today,
        expiration_date__lte=threshold,
    ).select_related("patient")

    count = expiring.count()

    if count == 0:
        logger.info("No consents expiring within the next 30 days.")
        return {"expiring_count": 0}

    logger.warning(
        "%d consent(s) expiring within 30 days.",
        count,
    )

    for consent in expiring.iterator():
        days_remaining = (consent.expiration_date - today).days
        logger.info(
            "Expiring consent: id=%s patient=%s purpose=%s expires=%s days_remaining=%d",
            consent.id,
            consent.patient_id,
            consent.purpose,
            consent.expiration_date,
            days_remaining,
        )

    return {"expiring_count": count}
