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
    return {
        "id": task.pk,
        "board": task.board_id,
        "column": task.column_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "assigned_to": [a.pk for a in task.assignees.all()],
        "due_date": task.due_date,
        "created_at": task.created_at,
        "order": task.order,
        "subtask_count": len(subtasks),
        "subtask_done_count": sum(1 for s in subtasks if s.done),
        "attachment_count": len(attachments),
        "labels": [serialize_label(label) for label in labels],
    }
