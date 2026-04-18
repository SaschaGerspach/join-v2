import logging
import threading

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_mail_async(**kwargs):
    kwargs.setdefault("fail_silently", False)

    def _send():
        try:
            send_mail(**kwargs)
        except Exception:
            logger.warning("Async mail failed: %s", kwargs.get("subject", ""), exc_info=True)

    threading.Thread(target=_send, daemon=True).start()
