from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.core.mail import send_mail, EmailMessage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def _send_mail_task(self, headers: dict[str, str] | None = None, **kwargs: Any) -> None:
    kwargs.setdefault("fail_silently", False)
    try:
        if headers:
            msg = EmailMessage(
                subject=kwargs.get("subject", ""),
                body=kwargs.get("message", ""),
                from_email=kwargs.get("from_email"),
                to=kwargs.get("recipient_list", []),
                headers=headers,
            )
            msg.send(fail_silently=kwargs.get("fail_silently", False))
        else:
            send_mail(**kwargs)
    except Exception as exc:
        logger.warning("Mail task failed: %s", kwargs.get("subject", ""), exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def send_mail_async(headers: dict[str, str] | None = None, **kwargs: Any) -> None:
    _send_mail_task.delay(headers=headers, **kwargs)
