import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder

from .models import Notification


def create_notification(recipient, notification_type, message, board_id=None, task_id=None):
    notification = Notification.objects.create(
        recipient=recipient,
        type=notification_type,
        message=message,
        board_id=board_id,
        task_id=task_id,
    )
    _push_notification(notification)
    return notification


def _push_notification(notification):
    channel_layer = get_channel_layer()
    data = {
        "id": notification.pk,
        "type": notification.type,
        "message": notification.message,
        "board_id": notification.board_id,
        "task_id": notification.task_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }
    safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
    async_to_sync(channel_layer.group_send)(
        f"user_{notification.recipient_id}",
        {
            "type": "user.notification",
            "payload": {
                "event": "new_notification",
                "data": safe_data,
            },
        },
    )
