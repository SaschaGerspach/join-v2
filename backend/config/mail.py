import logging
from concurrent.futures import ThreadPoolExecutor

from django.core.mail import send_mail, EmailMessage

logger = logging.getLogger(__name__)

_mail_executor = ThreadPoolExecutor(max_workers=3)


def send_mail_async(headers=None, **kwargs):
    kwargs.setdefault("fail_silently", False)

    def _send():
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
        except Exception:
            logger.warning("Async mail failed: %s", kwargs.get("subject", ""), exc_info=True)

    _mail_executor.submit(_send)
