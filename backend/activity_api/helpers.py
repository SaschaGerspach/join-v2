from __future__ import annotations

from auth_api.models import User
from boards_api.models import Board
from tasks_api.models import Task

from .models import ActivityEntry


def log_activity(
    board: Board,
    user: User,
    action: str,
    entity_type: str,
    entity_title: str,
    details: str = "",
    task: Task | None = None,
) -> None:
    ActivityEntry.objects.create(
        board=board,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_title=entity_title,
        details=details,
        task=task,
    )
