import logging
from concurrent.futures import ThreadPoolExecutor

from django.core.mail import send_mail

logger = logging.getLogger(__name__)

_mail_executor = ThreadPoolExecutor(max_workers=3)


def send_mail_async(**kwargs):
    kwargs.setdefault("fail_silently", False)

    def _send():
        try:
            send_mail(**kwargs)
        except Exception:
            logger.warning("Async mail failed: %s", kwargs.get("subject", ""), exc_info=True)

    _mail_executor.submit(_send)
