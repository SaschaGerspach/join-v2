import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from notifications_api.helpers import create_notification
from notifications_api.models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_due_date_reminders():
    from tasks_api.models import Task
    from tasks_api.views._notifications import _find_user_by_email

    hours = settings.DUE_DATE_REMINDER_HOURS
    now = timezone.now()
    deadline = (now + timedelta(hours=hours)).date()
    today = now.date()

    tasks = (
        Task.objects.filter(
            due_date__gte=today,
            due_date__lte=deadline,
            archived_at__isnull=True,
        )
        .select_related("board")
        .prefetch_related("assignees")
    )

    sent_count = 0
    for task in tasks:
        recipients = set()
        for contact in task.assignees.all():
            user = _find_user_by_email(contact.email)
            if user:
                recipients.add(user)

        for user in recipients:
            # Deduplicate: skip if a due-date reminder (identified by "due" in message) was already sent within the reminder window.
            already_notified = Notification.objects.filter(
                recipient=user,
                task_id=task.pk,
                type=Notification.Type.ASSIGNMENT,
                message__contains="due",
                created_at__gte=now - timedelta(hours=hours),
            ).exists()
            if already_notified:
                continue

            days_left = (task.due_date - today).days
            if days_left == 0:
                time_text = "today"
            elif days_left == 1:
                time_text = "tomorrow"
            else:
                time_text = f"in {days_left} days"

            create_notification(
                recipient=user,
                notification_type=Notification.Type.ASSIGNMENT,
                message=f'"{task.title}" is due {time_text}',
                board_id=task.board_id,
                task_id=task.pk,
            )
            sent_count += 1

    logger.info("Sent %d due-date reminders", sent_count)
    return sent_count
