from django.conf import settings

from config.mail import send_mail_async
from contacts_api.models import Contact
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


def _notify_comment(comment, actor):
    task = comment.task
    recipients = set()

    if task.assigned_to_id:
        try:
            contact = Contact.objects.get(pk=task.assigned_to_id)
            if contact.email:
                recipients.add(contact.email.lower())
        except Contact.DoesNotExist:
            pass

    if task.board.created_by_id != actor.id and task.board.created_by.email:
        recipients.add(task.board.created_by.email.lower())

    prior_authors = (
        Comment.objects.filter(task=task)
        .exclude(pk=comment.pk)
        .select_related("author")
    )
    for c in prior_authors:
        if c.author.email:
            recipients.add(c.author.email.lower())

    recipients.discard(actor.email.lower())

    if not recipients:
        return
    _notify(
        subject=f'New comment on "{_sanitize(task.title)}" — Join',
        body=(
            f'{_actor_name(actor)} commented on "{_sanitize(task.title)}":\n\n'
            f"{_sanitize(comment.text)}\n\n"
            f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
        ),
        recipients=list(recipients),
    )


def _notify_assignment(task, actor):
    if not task.assigned_to_id:
        return
    try:
        contact = Contact.objects.get(pk=task.assigned_to_id)
    except Contact.DoesNotExist:
        return
    if not contact.email or contact.email.lower() == actor.email.lower():
        return
    _notify(
        subject="You were assigned to a task — Join",
        body=(
            f'{_actor_name(actor)} assigned you to "{_sanitize(task.title)}" '
            f'on board "{_sanitize(task.board.title)}".\n\n'
            f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
        ),
        recipients=[contact.email],
    )
