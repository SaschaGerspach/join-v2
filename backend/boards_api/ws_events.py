from __future__ import annotations

import json
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder


def send_board_event(board_id: int, event_type: str, data: Any) -> None:
    channel_layer = get_channel_layer()
    safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
    async_to_sync(channel_layer.group_send)(
        f"board_{board_id}",
        {
            "type": "board.event",
            "payload": {
                "event": event_type,
                "data": safe_data,
            },
        },
    )
    try:
        from webhooks_api.dispatch import dispatch_event
        dispatch_event(board_id, event_type, safe_data)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Webhook dispatch failed for board %s", board_id, exc_info=True)
