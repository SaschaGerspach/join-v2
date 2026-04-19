from django.conf import settings
from django.db import models

from boards_api.models import Board


class ActivityEntry(models.Model):
    class Action(models.TextChoices):
        CREATED = "created"
        UPDATED = "updated"
        DELETED = "deleted"
        MOVED = "moved"

    class EntityType(models.TextChoices):
        TASK = "task"
        COLUMN = "column"
        COMMENT = "comment"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="activity")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_title = models.CharField(max_length=255)
    details = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
