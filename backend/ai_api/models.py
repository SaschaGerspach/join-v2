from django.conf import settings
from django.db import models

from .features import FEATURE_KEYS


class AIFeatureFlag(models.Model):
    """Per-feature on/off switch. A missing row means the feature is off, so the
    database default for every feature is disabled until an admin enables it."""

    key = models.CharField(max_length=64, unique=True)
    enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_feature_flags",
    )

    def __str__(self):
        return f"{self.key}: {'on' if self.enabled else 'off'}"

    @classmethod
    def is_enabled(cls, key):
        if key not in FEATURE_KEYS:
            return False
        return cls.objects.filter(key=key, enabled=True).exists()
