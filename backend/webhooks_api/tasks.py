import hashlib
import hmac
import json
import logging

import requests
from celery import shared_task
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

DELIVERY_TIMEOUT = 10


@shared_task(bind=True, max_retries=3)
def deliver_webhook(self, webhook_id, event_type, payload):
    from .models import Webhook, WebhookDelivery

    try:
        webhook = Webhook.objects.get(pk=webhook_id, is_active=True)
    except Webhook.DoesNotExist:
        return

    body = json.dumps(payload, cls=DjangoJSONEncoder)
    delivery = WebhookDelivery.objects.create(
        webhook=webhook,
        event_type=event_type,
        payload=payload,
        status=WebhookDelivery.Status.PENDING,
    )

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_type,
        "X-Delivery-Id": str(delivery.delivery_id),
    }

    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        resp = requests.post(
            webhook.url, data=body, headers=headers, timeout=DELIVERY_TIMEOUT
        )
        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:2000]
        if 200 <= resp.status_code < 300:
            delivery.status = WebhookDelivery.Status.SUCCESS
        else:
            delivery.status = WebhookDelivery.Status.FAILED
        delivery.save(update_fields=["response_status", "response_body", "status"])
    except requests.RequestException as exc:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.response_body = str(exc)[:2000]
        delivery.save(update_fields=["status", "response_body"])
        logger.warning("Webhook delivery %s failed: %s", delivery.delivery_id, exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
