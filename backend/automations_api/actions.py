import logging

from boards_api.ws_events import send_board_event
from notifications_api.helpers import create_notification
from tasks_api.views._helpers import serialize_task

from .models import ActionType

logger = logging.getLogger(__name__)


def execute_action(action, task, triggered_by):
    handler = _HANDLERS.get(action.action_type)
    if not handler:
        logger.warning("Unknown action type: %s", action.action_type)
        return False
    try:
        handler(task, action.config, triggered_by)
        return True
    except Exception:
        logger.exception("Action %s failed on task %s", action.action_type, task.pk)
        return False


def _action_move_to_column(task, config, triggered_by):
    column_id = config.get("column_id")
    if not column_id or task.column_id == column_id:
        return
    from columns_api.models import Column
    column = Column.objects.get(pk=column_id, board=task.board)
    task.column = column
    task.save(update_fields=["column"])
    send_board_event(task.board_id, "task_updated", serialize_task(task))


def _action_set_priority(task, config, triggered_by):
    priority = config.get("priority")
    if not priority or task.priority == priority:
        return
    task.priority = priority
    task.save(update_fields=["priority"])
    send_board_event(task.board_id, "task_updated", serialize_task(task))


def _action_assign_user(task, config, triggered_by):
    assignee_id = config.get("assignee_id")
    if not assignee_id:
        return
    task.assignees.add(assignee_id)
    send_board_event(task.board_id, "task_updated", serialize_task(task))


def _action_set_label(task, config, triggered_by):
    label_id = config.get("label_id")
    if not label_id:
        return
    task.labels.add(label_id)
    send_board_event(task.board_id, "task_updated", serialize_task(task))


def _action_remove_label(task, config, triggered_by):
    label_id = config.get("label_id")
    if not label_id:
        return
    task.labels.remove(label_id)
    send_board_event(task.board_id, "task_updated", serialize_task(task))


def _action_notify_creator(task, config, triggered_by):
    user = task.board.created_by
    create_notification(
        user, "automation",
        f"Automation: {task.title}",
        board_id=task.board_id, task_id=task.pk,
    )


def _action_notify_assignees(task, config, triggered_by):
    from contacts_api.models import Contact
    contacts = task.assignees.filter(user__isnull=False).select_related("user")
    for contact in contacts:
        create_notification(
            contact.user, "automation",
            f"Automation: {task.title}",
            board_id=task.board_id, task_id=task.pk,
        )


def _action_notify_user(task, config, triggered_by):
    from auth_api.models import User
    user_id = config.get("user_id")
    if not user_id:
        return
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    create_notification(
        user, "automation",
        f"Automation: {task.title}",
        board_id=task.board_id, task_id=task.pk,
    )


_HANDLERS = {
    ActionType.MOVE_TO_COLUMN: _action_move_to_column,
    ActionType.SET_PRIORITY: _action_set_priority,
    ActionType.ASSIGN_USER: _action_assign_user,
    ActionType.SET_LABEL: _action_set_label,
    ActionType.REMOVE_LABEL: _action_remove_label,
    ActionType.NOTIFY_CREATOR: _action_notify_creator,
    ActionType.NOTIFY_ASSIGNEES: _action_notify_assignees,
    ActionType.NOTIFY_USER: _action_notify_user,
}
