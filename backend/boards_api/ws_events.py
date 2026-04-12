from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_board_event(board_id, event_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"board_{board_id}",
        {
            "type": "board.event",
            "payload": {
                "event": event_type,
                "data": data,
            },
        },
    )
