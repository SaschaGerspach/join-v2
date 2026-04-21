from django.conf import settings
from django.db import models


class Board(models.Model):
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#29abe2')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boards",
    )
    team = models.ForeignKey(
        "teams_api.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boards",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BoardMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="board_memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.EDITOR)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["board", "user"], name="unique_board_member"),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.board.title}"


class BoardFavorite(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="board_favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["board", "user"], name="unique_board_favorite"),
        ]
