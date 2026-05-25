from .models import Webhook


def dispatch_event(board_id, event_type, payload):
    webhooks = Webhook.objects.filter(
        board_id=board_id,
        is_active=True,
    )
    for wh in webhooks:
        if event_type in wh.events:
            from .tasks import deliver_webhook
            deliver_webhook.delay(wh.pk, event_type, payload)
