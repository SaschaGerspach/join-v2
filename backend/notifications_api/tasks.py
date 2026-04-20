import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from config.mail import send_mail_async
from .models import Notification, NotificationPreference

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def send_daily_digest():
    cutoff = timezone.now() - timedelta(hours=24)
    prefs = NotificationPreference.objects.filter(email_delivery="digest").select_related("user")

    sent_count = 0
    for pref in prefs:
        notifications = Notification.objects.filter(
            recipient=pref.user,
            created_at__gte=cutoff,
            is_read=False,
        ).order_by("-created_at")[:50]

        if not notifications:
            continue

        lines = [f"- {n.message}" for n in notifications]
        body = (
            f"Hi {pref.user.first_name or pref.user.email},\n\n"
            f"You have {len(lines)} unread notification(s) from the last 24 hours:\n\n"
            + "\n".join(lines)
            + f"\n\nLog in to see details: {settings.FRONTEND_URL}/boards"
        )

        send_mail_async(
            subject=f"Your daily digest — {len(lines)} notification(s) | Join",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pref.user.email],
        )
        sent_count += 1

    logger.info("Sent %d daily digest emails", sent_count)
    return sent_count
