from django.conf import settings
from django.db import models


class TriggerType(models.TextChoices):
    TASK_MOVED_TO_COLUMN = "task_moved_to_column"
    TASK_CREATED = "task_created"
    PRIORITY_SET = "priority_set"
    ALL_SUBTASKS_DONE = "all_subtasks_done"
    DEADLINE_APPROACHING = "deadline_approaching"
    LABEL_ADDED = "label_added"


class ConditionType(models.TextChoices):
    PRIORITY_EQUALS = "priority_equals"
    LABEL_SET = "label_set"
    ASSIGNEE_EQUALS = "assignee_equals"


class ActionType(models.TextChoices):
    MOVE_TO_COLUMN = "move_to_column"
    SET_PRIORITY = "set_priority"
    ASSIGN_USER = "assign_user"
    SET_LABEL = "set_label"
    REMOVE_LABEL = "remove_label"
    NOTIFY_CREATOR = "notify_creator"
    NOTIFY_ASSIGNEES = "notify_assignees"
    NOTIFY_USER = "notify_user"


class AutomationRule(models.Model):
    board = models.ForeignKey(
        "boards_api.Board",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="automation_rules",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="automation_rules",
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    trigger_type = models.CharField(max_length=50, choices=TriggerType.choices)
    trigger_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RuleCondition(models.Model):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name="conditions")
    condition_type = models.CharField(max_length=50, choices=ConditionType.choices)
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.condition_type} on {self.rule.name}"


class RuleAction(models.Model):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    config = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.action_type} on {self.rule.name}"


class AutomationLog(models.Model):
    rule = models.ForeignKey(AutomationRule, on_delete=models.SET_NULL, null=True)
    task = models.ForeignKey("tasks_api.Task", on_delete=models.CASCADE, related_name="automation_logs")
    board = models.ForeignKey("boards_api.Board", on_delete=models.CASCADE)
    trigger_type = models.CharField(max_length=50)
    actions_executed = models.JSONField(default=list)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"Rule '{self.rule}' on task {self.task_id}"
