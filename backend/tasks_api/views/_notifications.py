from django.conf import settings
from django.contrib.auth import get_user_model

from config.mail import send_mail_async
from contacts_api.models import Contact
from notifications_api.helpers import create_notification
from notifications_api.models import Notification
from ..models import Comment


def _notify(subject, body, recipients):
    recipients = [r for r in {r.strip().lower() for r in recipients if r} if r]
    if not recipients:
        return
    send_mail_async(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
    )


def _sanitize(value):
    return value.replace('\n', '').replace('\r', '')


def _actor_name(user):
    return _sanitize(user.first_name or user.email)


def _find_user_by_email(email):
    if not email:
        return None
    User = get_user_model()
    try:
        return User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        return None


def _notify_comment(comment, actor):
    task = comment.task
    recipients = set()
    in_app_recipients = set()

    if task.assigned_to_id:
        try:
            contact = Contact.objects.get(pk=task.assigned_to_id)
            if contact.email:
                recipients.add(contact.email.lower())
                user = _find_user_by_email(contact.email)
                if user and user.pk != actor.pk:
                    in_app_recipients.add(user.pk)
        except Contact.DoesNotExist:
            pass

    if task.board.created_by_id != actor.id and task.board.created_by.email:
        recipients.add(task.board.created_by.email.lower())
        in_app_recipients.add(task.board.created_by_id)

    prior_authors = (
        Comment.objects.filter(task=task)
        .exclude(pk=comment.pk)
        .select_related("author")
    )
    for c in prior_authors:
        if c.author.email:
            recipients.add(c.author.email.lower())
        if c.author_id != actor.pk:
            in_app_recipients.add(c.author_id)

    recipients.discard(actor.email.lower())
    in_app_recipients.discard(actor.pk)

    if recipients:
        _notify(
            subject=f'New comment on "{_sanitize(task.title)}" — Join',
            body=(
                f'{_actor_name(actor)} commented on "{_sanitize(task.title)}":\n\n'
                f"{_sanitize(comment.text)}\n\n"
                f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
            ),
            recipients=list(recipients),
        )

    User = get_user_model()
    message = f'{_actor_name(actor)} commented on "{_sanitize(task.title)}"'
    for user_id in in_app_recipients:
        try:
            user = User.objects.get(pk=user_id)
            create_notification(
                recipient=user,
                notification_type=Notification.Type.COMMENT,
                message=message,
                board_id=task.board_id,
                task_id=task.pk,
            )
        except User.DoesNotExist:
            pass


def _notify_assignment(task, actor):
    if not task.assigned_to_id:
        return
    try:
        contact = Contact.objects.get(pk=task.assigned_to_id)
    except Contact.DoesNotExist:
        return

    is_self = contact.email and contact.email.lower() == actor.email.lower()

    if contact.email and not is_self:
        _notify(
            subject="You were assigned to a task — Join",
            body=(
                f'{_actor_name(actor)} assigned you to "{_sanitize(task.title)}" '
                f'on board "{_sanitize(task.board.title)}".\n\n'
                f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
            ),
            recipients=[contact.email],
        )

    user = _find_user_by_email(contact.email)
    if user and user.pk != actor.pk:
        create_notification(
            recipient=user,
            notification_type=Notification.Type.ASSIGNMENT,
            message=f'{_actor_name(actor)} assigned you to "{_sanitize(task.title)}"',
            board_id=task.board_id,
            task_id=task.pk,
        )
