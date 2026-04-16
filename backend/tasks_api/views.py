import re
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse
from django.urls import reverse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.views import _can_access
from boards_api.ws_events import send_board_event
from config.serializers import DetailSerializer
from columns_api.models import Column
from contacts_api.models import Contact
from .models import Task, Subtask, Comment, Label, Attachment
from .serializers import (
    AttachmentSerializer,
    AttachmentUploadSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    LabelCreateSerializer,
    LabelSerializer,
    LabelUpdateSerializer,
    SubtaskCreateSerializer,
    SubtaskSerializer,
    SubtaskUpdateSerializer,
    TaskCreateSerializer,
    TaskReorderItemSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)

ALLOWED_ATTACHMENT_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "txt", "md", "csv",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip",
}


def _notify(subject, body, recipients):
    recipients = [r for r in {r.strip().lower() for r in recipients if r} if r]
    if not recipients:
        return
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )


def _sanitize(value):
    return value.replace('\n', '').replace('\r', '')


def _actor_name(user):
    return _sanitize(user.first_name or user.email)


def _notify_comment(comment, actor):
    task = comment.task
    recipients = set()

    if task.assigned_to_id:
        try:
            contact = Contact.objects.get(pk=task.assigned_to_id)
            if contact.email:
                recipients.add(contact.email.lower())
        except Contact.DoesNotExist:
            pass

    if task.board.created_by_id != actor.id and task.board.created_by.email:
        recipients.add(task.board.created_by.email.lower())

    prior_authors = (
        Comment.objects.filter(task=task)
        .exclude(pk=comment.pk)
        .select_related("author")
    )
    for c in prior_authors:
        if c.author.email:
            recipients.add(c.author.email.lower())

    recipients.discard(actor.email.lower())

    if not recipients:
        return
    _notify(
        subject=f'New comment on "{_sanitize(task.title)}" — Join',
        body=(
            f'{_actor_name(actor)} commented on "{_sanitize(task.title)}":\n\n'
            f"{_sanitize(comment.text)}\n\n"
            f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
        ),
        recipients=list(recipients),
    )


def _notify_assignment(task, actor):
    if not task.assigned_to_id:
        return
    try:
        contact = Contact.objects.get(pk=task.assigned_to_id)
    except Contact.DoesNotExist:
        return
    if not contact.email or contact.email.lower() == actor.email.lower():
        return
    _notify(
        subject="You were assigned to a task — Join",
        body=(
            f'{_actor_name(actor)} assigned you to "{_sanitize(task.title)}" '
            f'on board "{_sanitize(task.board.title)}".\n\n'
            f"Open: {settings.FRONTEND_URL}/boards/{task.board_id}"
        ),
        recipients=[contact.email],
    )


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
        "attachment_count": task.attachments.count(),
        "labels": [serialize_label(label) for label in task.labels.all()],
    }


@extend_schema(
    methods=["GET"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: TaskSerializer(many=True), 400: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    request=TaskCreateSerializer,
    responses={201: TaskSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
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

    column_id = request.data.get("column")
    if not column_id:
        first_column = board.columns.order_by("order").first()
        column_id = first_column.pk if first_column else None
    elif not Column.objects.filter(pk=column_id, board=board).exists():
        return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)

    assigned_to_id = request.data.get("assigned_to")
    if assigned_to_id and not Contact.objects.filter(pk=assigned_to_id, owner=request.user).exists():
        return Response({"detail": "Invalid contact."}, status=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(
        board=board,
        title=title,
        description=request.data.get("description", ""),
        priority=request.data.get("priority", Task.Priority.MEDIUM),
        column_id=column_id,
        assigned_to_id=assigned_to_id,
        due_date=request.data.get("due_date"),
    )
    _notify_assignment(task, request.user)
    data = serialize_task(task)
    send_board_event(board.pk, "task_created", data)
    return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    responses={200: TaskSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=TaskUpdateSerializer,
    responses={200: TaskSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
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
        if "assigned_to" in request.data and request.data["assigned_to"]:
            if not Contact.objects.filter(pk=request.data["assigned_to"], owner=request.user).exists():
                return Response({"detail": "Invalid contact."}, status=status.HTTP_400_BAD_REQUEST)
        if "column" in request.data and request.data["column"]:
            if not Column.objects.filter(pk=request.data["column"], board=task.board).exists():
                return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)
        previous_assignee_id = task.assigned_to_id
        for field in ["title", "description", "priority", "column", "assigned_to", "due_date", "order"]:
            key = field if field not in ["column", "assigned_to"] else f"{field}_id"
            if field in request.data:
                setattr(task, key, request.data[field])
        task.save()
        if "label_ids" in request.data:
            task.labels.set(Label.objects.filter(pk__in=request.data["label_ids"], board=task.board))
        if task.assigned_to_id and task.assigned_to_id != previous_assignee_id:
            _notify_assignment(task, request.user)
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


@extend_schema(
    methods=["GET"],
    responses={200: SubtaskSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=SubtaskCreateSerializer,
    responses={201: SubtaskSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
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


@extend_schema(
    methods=["PATCH"],
    request=SubtaskUpdateSerializer,
    responses={200: SubtaskSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
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


@extend_schema(
    request=TaskReorderItemSerializer(many=True),
    responses={204: None, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["POST"])
def task_reorder(request):
    items = request.data
    if not isinstance(items, list):
        return Response({"detail": "Expected a list."}, status=status.HTTP_400_BAD_REQUEST)

    task_ids = [item["id"] for item in items if "id" in item]
    fetched = list(Task.objects.filter(pk__in=task_ids).select_related("board"))
    if len(fetched) != len(set(task_ids)):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    for t in fetched:
        if not _can_access(t.board, request.user):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
    tasks = {t.pk: t for t in fetched}

    board_ids = {t.board_id for t in fetched}
    valid_columns = set(Column.objects.filter(board_id__in=board_ids).values_list("pk", flat=True))

    for item in items:
        task = tasks.get(item.get("id"))
        if not task:
            continue
        if "order" in item:
            task.order = item["order"]
        if "column" in item:
            if item["column"] not in valid_columns:
                return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)
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


@extend_schema(
    methods=["GET"],
    responses={200: CommentSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=CommentCreateSerializer,
    responses={201: CommentSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
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
    _notify_comment(comment, request.user)
    return Response(serialize_comment(comment), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=CommentCreateSerializer,
    responses={200: CommentSerializer, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
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


@extend_schema(
    methods=["GET"],
    responses={200: LabelSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=LabelCreateSerializer,
    responses={201: LabelSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "POST"])
def label_list(request, board_pk):
    try:
        board = Board.objects.get(pk=board_pk)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_label(label) for label in board.labels.all()])

    name = request.data.get("name", "").strip()
    color = request.data.get("color", "#29abe2").strip()
    if not name:
        return Response({"detail": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        return Response({"detail": "Invalid color."}, status=status.HTTP_400_BAD_REQUEST)

    label, created = Label.objects.get_or_create(board=board, name=name, defaults={"color": color})
    if not created:
        return Response({"detail": "Label already exists."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serialize_label(label), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=LabelUpdateSerializer,
    responses={200: LabelSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
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
            color = request.data["color"].strip()
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                return Response({"detail": "Invalid color."}, status=status.HTTP_400_BAD_REQUEST)
            label.color = color
        label.save()
        return Response(serialize_label(label))

    label.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def serialize_attachment(att, request):
    download_url = reverse("tasks_api:attachment-download", kwargs={"task_pk": att.task_id, "pk": att.pk})
    try:
        size = att.file.size
    except (OSError, ValueError):
        size = 0
    return {
        "id": att.pk,
        "filename": att.filename,
        "url": request.build_absolute_uri(download_url),
        "size": size,
        "uploaded_at": att.uploaded_at,
    }


@extend_schema(
    methods=["GET"],
    responses={200: AttachmentSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request={"multipart/form-data": AttachmentUploadSerializer},
    responses={201: AttachmentSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
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

    ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return Response(
            {"detail": "File type not allowed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    safe_name = re.sub(r'[^\w.\-]', '_', file.name)
    file.name = f"{uuid.uuid4().hex}_{safe_name}"
    att = Attachment.objects.create(task=task, file=file, filename=safe_name)
    send_board_event(task.board_id, "task_updated", serialize_task(task))
    return Response(serialize_attachment(att, request), status=status.HTTP_201_CREATED)


@extend_schema(responses={204: None, 404: DetailSerializer})
@api_view(["DELETE"])
def attachment_detail(request, task_pk, pk):
    try:
        att = Attachment.objects.get(pk=pk, task_id=task_pk)
    except Attachment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(att.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    task = att.task
    att.file.delete()
    att.delete()
    send_board_event(task.board_id, "task_updated", serialize_task(task))
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses={
        (200, "application/octet-stream"): bytes,
        404: DetailSerializer,
    },
)
@api_view(["GET"])
def attachment_download(request, task_pk, pk):
    try:
        att = Attachment.objects.select_related("task__board").get(pk=pk, task_id=task_pk)
    except Attachment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(att.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    return FileResponse(att.file.open("rb"), as_attachment=True, filename=att.filename)
