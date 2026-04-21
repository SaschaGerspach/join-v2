import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import AuditLog

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90


@shared_task
def cleanup_old_audit_logs():
    cutoff = timezone.now() - timedelta(days=RETENTION_DAYS)
    count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Deleted %d audit log entries older than %d days", count, RETENTION_DAYS)
    return count
