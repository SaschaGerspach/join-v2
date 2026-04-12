from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.views import _can_access
from boards_api.ws_events import send_board_event
from .models import Task, Subtask, Comment, Label, Attachment


def serialize_label(label):
    return {"id": label.pk, "name": label.name, "color": label.color}


def serialize_task(task):
    subtasks = task.subtasks.all()
    return {
        "id": task.pk,
        "board": task.board_id,
        "column": task.column_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "assigned_to": task.assigned_to_id,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "order": task.order,
        "subtask_count": subtasks.count(),
        "subtask_done_count": subtasks.filter(done=True).count(),
        "labels": [serialize_label(l) for l in task.labels.all()],
    }


@api_view(["GET", "POST"])
def task_list(request):
    board_id = request.query_params.get("board")

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        board = Board.objects.get(pk=board_id)
    except Board.DoesNotExist:
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(board, request.user):
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        tasks = board.tasks.all().order_by("order", "created_at")
        return Response([serialize_task(t) for t in tasks])

    title = request.data.get("title", "").strip()
    if not title:
        return Response({"detail": "Title is required."}, status=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(
        board=board,
        title=title,
        description=request.data.get("description", ""),
        priority=request.data.get("priority", Task.Priority.MEDIUM),
        column_id=request.data.get("column"),
        assigned_to_id=request.data.get("assigned_to"),
        due_date=request.data.get("due_date"),
    )
    data = serialize_task(task)
    send_board_event(board.pk, "task_created", data)
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_task(task))

    if request.method == "PATCH":
        for field in ["title", "description", "priority", "column", "assigned_to", "due_date", "order"]:
            key = field if field not in ["column", "assigned_to"] else f"{field}_id"
            if field in request.data:
                setattr(task, key, request.data[field])
        task.save()
        if "label_ids" in request.data:
            task.labels.set(Label.objects.filter(pk__in=request.data["label_ids"], board=task.board))
        data = serialize_task(task)
        send_board_event(task.board_id, "task_updated", data)
        return Response(data)

    board_id = task.board_id
    task_id = task.pk
    task.delete()
    send_board_event(board_id, "task_deleted", {"id": task_id})
    return Response(status=status.HTTP_204_NO_CONTENT)


def serialize_subtask(subtask):
    return {
        "id": subtask.pk,
        "task": subtask.task_id,
        "title": subtask.title,
        "done": subtask.done,
    }


@api_view(["GET", "POST"])
def subtask_list(request, task_pk):
    try:
        task = Task.objects.get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(task.board, request.user):
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_subtask(s) for s in task.subtasks.all()])

    title = request.data.get("title", "").strip()
    if not title:
        return Response({"detail": "Title is required."}, status=status.HTTP_400_BAD_REQUEST)

    subtask = Subtask.objects.create(task=task, title=title)
    return Response(serialize_subtask(subtask), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def subtask_detail(request, task_pk, pk):
    try:
        subtask = Subtask.objects.get(pk=pk, task_id=task_pk)
    except Subtask.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(subtask.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        if "title" in request.data:
            subtask.title = request.data["title"].strip()
        if "done" in request.data:
            subtask.done = request.data["done"]
        subtask.save()
        return Response(serialize_subtask(subtask))

    subtask.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def task_reorder(request):
    items = request.data
    if not isinstance(items, list):
        return Response({"detail": "Expected a list."}, status=status.HTTP_400_BAD_REQUEST)

    task_ids = [item["id"] for item in items if "id" in item]
    tasks = {
        t.pk: t for t in Task.objects.filter(pk__in=task_ids)
        if _can_access(t.board, request.user)
    }

    for item in items:
        task = tasks.get(item.get("id"))
        if not task:
            continue
        if "order" in item:
            task.order = item["order"]
        if "column" in item:
            task.column_id = item["column"]

    Task.objects.bulk_update(list(tasks.values()), ["order", "column_id"])

    board_ids = {t.board_id for t in tasks.values()}
    for bid in board_ids:
        board_tasks = [serialize_task(t) for t in tasks.values() if t.board_id == bid]
        send_board_event(bid, "tasks_reordered", board_tasks)

    return Response(status=status.HTTP_204_NO_CONTENT)


def serialize_comment(comment):
    return {
        "id": comment.pk,
        "task": comment.task_id,
        "author_id": comment.author_id,
        "author_name": f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.email,
        "text": comment.text,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@api_view(["GET", "POST"])
def comment_list(request, task_pk):
    try:
        task = Task.objects.get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(task.board, request.user):
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_comment(c) for c in task.comments.select_related("author").all()])

    text = request.data.get("text", "").strip()
    if not text:
        return Response({"detail": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)

    comment = Comment.objects.create(task=task, author=request.user, text=text)
    return Response(serialize_comment(comment), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def comment_detail(request, task_pk, pk):
    try:
        comment = Comment.objects.select_related("author").get(pk=pk, task_id=task_pk)
    except Comment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if comment.author != request.user:
        return Response({"detail": "You can only edit your own comments."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"detail": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)
        comment.text = text
        comment.save(update_fields=["text", "updated_at"])
        return Response(serialize_comment(comment))

    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def label_list(request, board_pk):
    try:
        board = Board.objects.get(pk=board_pk)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_label(l) for l in board.labels.all()])

    name = request.data.get("name", "").strip()
    color = request.data.get("color", "#29abe2").strip()
    if not name:
        return Response({"detail": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)

    label, created = Label.objects.get_or_create(board=board, name=name, defaults={"color": color})
    if not created:
        return Response({"detail": "Label already exists."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serialize_label(label), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def label_detail(request, board_pk, pk):
    try:
        label = Label.objects.get(pk=pk, board_id=board_pk)
    except Label.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(label.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        if "name" in request.data:
            label.name = request.data["name"].strip()
        if "color" in request.data:
            label.color = request.data["color"].strip()
        label.save()
        return Response(serialize_label(label))

    label.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def serialize_attachment(att, request):
    return {
        "id": att.pk,
        "filename": att.filename,
        "url": request.build_absolute_uri(att.file.url),
        "uploaded_at": att.uploaded_at,
    }


@api_view(["GET", "POST"])
def attachment_list(request, task_pk):
    try:
        task = Task.objects.get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(task.board, request.user):
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_attachment(a, request) for a in task.attachments.all()])

    file = request.FILES.get("file")
    if not file:
        return Response({"detail": "File is required."}, status=status.HTTP_400_BAD_REQUEST)
    if file.size > 5 * 1024 * 1024:
        return Response({"detail": "File too large (max 5MB)."}, status=status.HTTP_400_BAD_REQUEST)

    att = Attachment.objects.create(task=task, file=file, filename=file.name)
    return Response(serialize_attachment(att, request), status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def attachment_detail(request, task_pk, pk):
    try:
        att = Attachment.objects.get(pk=pk, task_id=task_pk)
    except Attachment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(att.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    att.file.delete()
    att.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
