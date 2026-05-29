from __future__ import annotations

from typing import Any

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


# Rules are evaluated synchronously in the request cycle on purpose, not by
# oversight. Moving this to a Celery task (via transaction.on_commit) is viable
# for latency, but REQUIRES replacing the thread-local _loop_guard in engine.py
# with a distributed guard (e.g. Redis): action-triggered follow-up signals
# would then run in separate worker tasks, where the thread-local guard no
# longer prevents trigger-chain re-entry across task boundaries.


@receiver(task_created)
def on_task_created(sender: type, task: Any, **kwargs: Any) -> None:
    evaluate_rules(task, TriggerType.TASK_CREATED)


@receiver(task_moved)
def on_task_moved(sender: type, task: Any, column_id: int, **kwargs: Any) -> None:
    evaluate_rules(task, TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": column_id})


@receiver(task_priority_changed)
def on_task_priority_changed(sender: type, task: Any, priority: str, **kwargs: Any) -> None:
    evaluate_rules(task, TriggerType.PRIORITY_SET, {"priority": priority})


@receiver(task_label_added)
def on_task_label_added(sender: type, task: Any, label_id: int, **kwargs: Any) -> None:
    evaluate_rules(task, TriggerType.LABEL_ADDED, {"label_id": label_id})


@receiver(all_subtasks_completed)
def on_all_subtasks_completed(sender: type, task: Any, **kwargs: Any) -> None:
    evaluate_rules(task, TriggerType.ALL_SUBTASKS_DONE)
