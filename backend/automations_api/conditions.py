from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .models import ConditionType, RuleCondition

if TYPE_CHECKING:
    from collections.abc import Callable

    from tasks_api.models import Task


def check_condition(condition: RuleCondition, task: Task) -> bool:
    checker = _CHECKERS.get(condition.condition_type)
    if not checker:
        return False
    return checker(task, condition.config)


def _priority_equals(task: Task, config: dict[str, Any]) -> bool:
    return task.priority == config.get("priority")


def _label_set(task: Task, config: dict[str, Any]) -> bool:
    label_id = config.get("label_id")
    if not label_id:
        return False
    return task.labels.filter(pk=label_id).exists()


def _assignee_equals(task: Task, config: dict[str, Any]) -> bool:
    assignee_id = config.get("assignee_id")
    if not assignee_id:
        return False
    return task.assignees.filter(pk=assignee_id).exists()


_CHECKERS: dict[str, Callable[[Task, dict[str, Any]], bool]] = {
    ConditionType.PRIORITY_EQUALS: _priority_equals,
    ConditionType.LABEL_SET: _label_set,
    ConditionType.ASSIGNEE_EQUALS: _assignee_equals,
}
