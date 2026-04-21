from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "login_success"
        LOGIN_FAILED = "login_failed"
        PASSWORD_RESET = "password_reset"
        TOTP_ENABLED = "totp_enabled"
        TOTP_DISABLED = "totp_disabled"
        BOARD_MEMBER_ADDED = "board_member_added"
        BOARD_MEMBER_REMOVED = "board_member_removed"
        BOARD_MEMBER_ROLE_CHANGED = "board_member_role_changed"
        TEAM_MEMBER_ADDED = "team_member_added"
        TEAM_MEMBER_REMOVED = "team_member_removed"
        TEAM_MEMBER_ROLE_CHANGED = "team_member_role_changed"
        ACCOUNT_DELETED = "account_deleted"
        ADMIN_ACTION = "admin_action"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs",
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    detail = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["event_type", "created_at"])]

    def __str__(self):
        return f"{self.event_type} — {self.user} — {self.created_at:%Y-%m-%d %H:%M}"
