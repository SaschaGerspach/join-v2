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
    board = models.ForeignKey(
        "boards_api.Board",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    task = models.ForeignKey(
        "tasks_api.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    disabled_types = models.JSONField(default=list, blank=True)
    muted_boards = models.ManyToManyField(
        "boards_api.Board",
        blank=True,
        related_name="+",
    )
