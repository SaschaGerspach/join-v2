from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from boards_api.models import Board
from columns_api.models import Column


def _private_storage():
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Recurrence(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Biweekly"
        MONTHLY = "monthly", "Monthly"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    column = models.ForeignKey(Column, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assignees = models.ManyToManyField(
        "contacts_api.Contact",
        blank=True,
        related_name="assigned_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.CharField(max_length=10, choices=Recurrence.choices, null=True, blank=True, default=None)
    labels = models.ManyToManyField('Label', blank=True, related_name="tasks")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["board", "order"])]

    def __str__(self):
        return self.title


class Label(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="labels")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#29abe2')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["board", "name"], name="unique_label_per_board"),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=255)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        "auth_api.User",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.email} on {self.task.title}"


def attachment_path(instance, filename):
    return f"attachments/task_{instance.task_id}/{filename}"


class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_path, storage=_private_storage)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dependencies")
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dependents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "depends_on"], name="unique_task_dependency"),
        ]


class CustomField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        SELECT = "select", "Select"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="custom_fields")
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=10, choices=FieldType.choices)
    options = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["board", "name"], name="unique_custom_field_per_board"),
        ]
        ordering = ["order", "pk"]


class TaskFieldValue(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="field_values")
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name="values")
    value = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "field"], name="unique_task_field_value"),
        ]


class TimeEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_entries")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="time_entries",
    )
    duration_minutes = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True, default="")
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_at"]
