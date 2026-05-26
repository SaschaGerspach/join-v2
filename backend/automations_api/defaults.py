from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ActionType, AutomationRule, RuleAction, TriggerType

if TYPE_CHECKING:
    from auth_api.models import User
    from boards_api.models import Board


def create_default_rules(board: Board, user: User) -> None:
    rule1 = AutomationRule.objects.create(
        board=board,
        created_by=user,
        name="Notify when all subtasks done",
        trigger_type=TriggerType.ALL_SUBTASKS_DONE,
        is_default=True,
    )
    RuleAction.objects.create(
        rule=rule1,
        action_type=ActionType.NOTIFY_ASSIGNEES,
        order=0,
    )

    rule2 = AutomationRule.objects.create(
        board=board,
        created_by=user,
        name="Set urgent priority near deadline",
        trigger_type=TriggerType.DEADLINE_APPROACHING,
        trigger_config={"hours": 24},
        is_default=True,
    )
    RuleAction.objects.create(
        rule=rule2,
        action_type=ActionType.SET_PRIORITY,
        config={"priority": "urgent"},
        order=0,
    )
