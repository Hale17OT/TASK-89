import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medrights.settings.development")

app = Celery("medrights")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "auto-close-unpaid-orders": {
        "task": "apps.financials.tasks.auto_close_unpaid_orders",
        "schedule": 60.0,
    },
    "daily-reconciliation": {
        "task": "apps.financials.tasks.generate_daily_reconciliation",
        "schedule": crontab(hour=23, minute=59),
    },
    "process-report-subscriptions": {
        "task": "apps.reports.tasks.process_due_subscriptions",
        "schedule": 300.0,
    },
    "retry-failed-outbox": {
        "task": "apps.reports.tasks.retry_failed_outbox_items",
        "schedule": 300.0,
    },
    "cleanup-expired-sessions": {
        "task": "apps.accounts.tasks.cleanup_expired_sessions",
        "schedule": 3600.0,
    },
    "check-expiring-consents": {
        "task": "apps.consent.tasks.check_expiring_consents",
        "schedule": crontab(hour=6, minute=0),
    },
    "maintain-audit-partitions": {
        "task": "apps.audit.tasks.maintain_partitions",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
    "archive-old-audit-entries": {
        "task": "apps.audit.tasks.archive_old_entries",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
