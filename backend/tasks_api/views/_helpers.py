from datetime import timedelta
from dateutil.relativedelta import relativedelta

ALLOWED_ATTACHMENT_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "txt", "md", "csv",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip",
}


def serialize_label(label):
    return {"id": label.pk, "name": label.name, "color": label.color}


def serialize_task(task):
    subtasks = list(task.subtasks.all())
    attachments = list(task.attachments.all())
    labels = list(task.labels.all())
    dependencies = list(task.dependencies.select_related("depends_on").all())
    return {
        "id": task.pk,
        "board": task.board_id,
        "column": task.column_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "assigned_to": [a.pk for a in task.assignees.all()],
        "due_date": task.due_date,
        "recurrence": task.recurrence,
        "created_at": task.created_at,
        "order": task.order,
        "subtask_count": len(subtasks),
        "subtask_done_count": sum(1 for s in subtasks if s.done),
        "attachment_count": len(attachments),
        "labels": [serialize_label(label) for label in labels],
        "dependencies": [{"id": d.pk, "depends_on": d.depends_on_id, "title": d.depends_on.title} for d in dependencies],
    }


def next_due_date(current_date, recurrence):
    if recurrence == "daily":
        return current_date + timedelta(days=1)
    if recurrence == "weekly":
        return current_date + timedelta(weeks=1)
    if recurrence == "biweekly":
        return current_date + timedelta(weeks=2)
    if recurrence == "monthly":
        return current_date + relativedelta(months=1)
    return None


def create_next_recurring_task(task):
    if not task.recurrence or not task.due_date:
        return None
    from ..models import Task
    new_due = next_due_date(task.due_date, task.recurrence)
    if not new_due:
        return None
    first_column = task.board.columns.order_by("order").first()
    new_task = Task.objects.create(
        board=task.board,
        column=first_column,
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=new_due,
        recurrence=task.recurrence,
        order=0,
    )
    new_task.assignees.set(task.assignees.all())
    new_task.labels.set(task.labels.all())
    return new_task
