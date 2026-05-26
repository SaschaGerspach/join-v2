from __future__ import annotations

from typing import Any

from .models import Webhook


def dispatch_event(board_id: int, event_type: str, payload: dict[str, Any]) -> None:
    webhooks = Webhook.objects.filter(
        board_id=board_id,
        is_active=True,
    )
    for wh in webhooks:
        if event_type in wh.events:
            from .tasks import deliver_webhook
            deliver_webhook.delay(wh.pk, event_type, payload)
