import uuid

from django.db import models

from boards_api.models import Board


class EventType(models.TextChoices):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_MOVED = "task_moved"
    COMMENT_ADDED = "comment_added"


ALL_EVENTS = [e.value for e in EventType]


class Webhook(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="webhooks")
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64, default="", blank=True)
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["board", "url"], name="unique_webhook_per_board"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.url} ({self.board})"


class WebhookDelivery(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success"
        FAILED = "failed"
        PENDING = "pending"

    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=30)
    payload = models.JSONField()
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempted_at = models.DateTimeField(auto_now_add=True)
    delivery_id = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["webhook", "-attempted_at"]),
        ]
