import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from config.mail import send_mail_async

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def send_password_reset_email(email: str) -> None:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    send_mail_async(
        subject="Password Reset — Join",
        message=f"Click the link to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def delete_expired_guest_accounts() -> int:
    cutoff = timezone.now() - settings.GUEST_ACCOUNT_TTL
    # Hard delete: cascades to the guest's boards, contacts and demo teammates' data.
    # A deleted user also invalidates any refresh token still held by the browser.
    expired = User.objects.filter(is_guest=True, date_joined__lt=cutoff)
    count = expired.count()
    expired.delete()
    logger.info("Deleted %d expired guest accounts", count)
    return count
