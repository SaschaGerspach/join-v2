from django.dispatch import receiver

from tasks_api.signals import (
    all_subtasks_completed,
    task_created,
    task_label_added,
    task_moved,
    task_priority_changed,
)

from .engine import evaluate_rules
from .models import TriggerType


@receiver(task_created)
def on_task_created(sender, task, **kwargs):
    evaluate_rules(task, TriggerType.TASK_CREATED)


@receiver(task_moved)
def on_task_moved(sender, task, column_id, **kwargs):
    evaluate_rules(task, TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": column_id})


@receiver(task_priority_changed)
def on_task_priority_changed(sender, task, priority, **kwargs):
    evaluate_rules(task, TriggerType.PRIORITY_SET, {"priority": priority})


@receiver(task_label_added)
def on_task_label_added(sender, task, label_id, **kwargs):
    evaluate_rules(task, TriggerType.LABEL_ADDED, {"label_id": label_id})


@receiver(all_subtasks_completed)
def on_all_subtasks_completed(sender, task, **kwargs):
    evaluate_rules(task, TriggerType.ALL_SUBTASKS_DONE)
