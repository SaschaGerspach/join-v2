from django.db import models

from boards_api.models import Board
from columns_api.models import Column


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    column = models.ForeignKey(Column, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_to = models.ForeignKey(
        "contacts_api.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    labels = models.ManyToManyField('Label', blank=True, related_name="tasks")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Label(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="labels")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#29abe2')

    class Meta:
        unique_together = ("board", "name")
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
    file = models.FileField(upload_to=attachment_path)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
