from django.conf import settings
from django.db import models


class Board(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boards",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
