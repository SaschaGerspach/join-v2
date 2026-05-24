from .models import ConditionType


def check_condition(condition, task):
    checker = _CHECKERS.get(condition.condition_type)
    if not checker:
        return False
    return checker(task, condition.config)


def _priority_equals(task, config):
    return task.priority == config.get("priority")


def _label_set(task, config):
    label_id = config.get("label_id")
    if not label_id:
        return False
    return task.labels.filter(pk=label_id).exists()


def _assignee_equals(task, config):
    assignee_id = config.get("assignee_id")
    if not assignee_id:
        return False
    return task.assignees.filter(pk=assignee_id).exists()


_CHECKERS = {
    ConditionType.PRIORITY_EQUALS: _priority_equals,
    ConditionType.LABEL_SET: _label_set,
    ConditionType.ASSIGNEE_EQUALS: _assignee_equals,
}
