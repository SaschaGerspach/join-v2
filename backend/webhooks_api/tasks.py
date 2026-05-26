import hashlib
import hmac
import json
import logging

import requests
from celery import shared_task
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

DELIVERY_TIMEOUT = 10

EVENT_LABELS = {
    "task_created": "Task Created",
    "task_updated": "Task Updated",
    "task_deleted": "Task Deleted",
    "task_moved": "Task Moved",
    "comment_added": "Comment Added",
}


def _is_slack_url(url: str) -> bool:
    return "hooks.slack.com" in url


def _is_teams_url(url: str) -> bool:
    return "webhook.office.com" in url or "webhook.office365.com" in url


def _format_slack_payload(event_type: str, payload: dict) -> dict:
    title = payload.get("title", "")
    board = payload.get("board_title", "")
    label = EVENT_LABELS.get(event_type, event_type)
    text = f"*{label}*: {title}"
    if board:
        text += f" (Board: {board})"
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": text}},
    ]
    fields = []
    if payload.get("priority"):
        fields.append({"type": "mrkdwn", "text": f"*Priority:* {payload['priority']}"})
    if payload.get("column_title"):
        fields.append({"type": "mrkdwn", "text": f"*Column:* {payload['column_title']}"})
    if fields:
        blocks.append({"type": "section", "fields": fields})
    return {"blocks": blocks, "text": text}


def _format_teams_payload(event_type: str, payload: dict) -> dict:
    title = payload.get("title", "")
    board = payload.get("board_title", "")
    label = EVENT_LABELS.get(event_type, event_type)
    facts = []
    if payload.get("priority"):
        facts.append({"name": "Priority", "value": payload["priority"]})
    if payload.get("column_title"):
        facts.append({"name": "Column", "value": payload["column_title"]})
    if board:
        facts.append({"name": "Board", "value": board})
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": f"{label}: {title}",
        "themeColor": "29abe2",
        "title": label,
        "sections": [{
            "activityTitle": title,
            "facts": facts,
        }],
    }


@shared_task(bind=True, max_retries=3)
def deliver_webhook(self, webhook_id, event_type, payload):
    from .models import Webhook, WebhookDelivery

    try:
        webhook = Webhook.objects.get(pk=webhook_id, is_active=True)
    except Webhook.DoesNotExist:
        return

    if _is_slack_url(webhook.url):
        formatted_payload = _format_slack_payload(event_type, payload)
    elif _is_teams_url(webhook.url):
        formatted_payload = _format_teams_payload(event_type, payload)
    else:
        formatted_payload = payload

    body = json.dumps(formatted_payload, cls=DjangoJSONEncoder)
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
