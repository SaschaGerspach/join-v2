from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ASSIGNMENT = "assignment"
        COMMENT = "comment"
        MENTION = "mention"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.CharField(max_length=500)
    board_id = models.PositiveIntegerField(null=True, blank=True)
    task_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
