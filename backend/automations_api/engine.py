import logging
import threading

from .actions import execute_action
from .conditions import check_condition
from .models import AutomationLog, AutomationRule

logger = logging.getLogger(__name__)

_loop_guard = threading.local()


def evaluate_rules(task, trigger_type, context=None):
    if context is None:
        context = {}

    if not hasattr(_loop_guard, "active"):
        _loop_guard.active = set()

    board = task.board
    rules = (
        AutomationRule.objects
        .filter(trigger_type=trigger_type, is_active=True)
        .filter(models_q_board_or_global(board.pk))
        .prefetch_related("conditions", "actions")
    )

    for rule in rules:
        guard_key = (rule.pk, task.pk)
        if guard_key in _loop_guard.active:
            logger.debug("Loop guard: skipping rule %s for task %s", rule.pk, task.pk)
            continue

        if not _trigger_matches(rule, context):
            continue

        if not all(check_condition(c, task) for c in rule.conditions.all()):
            continue

        _loop_guard.active.add(guard_key)
        try:
            _execute_rule(rule, task)
        finally:
            _loop_guard.active.discard(guard_key)


def _trigger_matches(rule, context):
    config = rule.trigger_config
    if not config:
        return True

    if rule.trigger_type == "task_moved_to_column":
        return context.get("column_id") == config.get("column_id")

    if rule.trigger_type == "priority_set":
        return context.get("priority") == config.get("priority")

    if rule.trigger_type == "label_added":
        return context.get("label_id") == config.get("label_id")

    if rule.trigger_type == "deadline_approaching":
        return True

    return True


def _execute_rule(rule, task):
    executed = []
    for action in rule.actions.all():
        if execute_action(action, task, rule.created_by):
            executed.append(action.action_type)

    if executed:
        AutomationLog.objects.create(
            rule=rule,
            task=task,
            board=task.board,
            trigger_type=rule.trigger_type,
            actions_executed=executed,
        )
        from boards_api.ws_events import send_board_event
        send_board_event(task.board_id, "automation_executed", {
            "rule_name": rule.name,
            "task_id": task.pk,
            "actions": executed,
        })


def models_q_board_or_global(board_id):
    from django.db.models import Q
    return Q(board_id=board_id) | Q(board__isnull=True)
