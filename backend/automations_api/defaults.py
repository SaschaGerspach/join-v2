from .models import ActionType, AutomationRule, RuleAction, TriggerType


def create_default_rules(board, user):
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
