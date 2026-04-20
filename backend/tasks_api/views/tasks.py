from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.permissions import can_access_board, can_edit_board, get_board_or_404
from boards_api.ws_events import send_board_event
from columns_api.models import Column
from config.serializers import DetailSerializer
from contacts_api.models import Contact
from ..models import Task, Label
from ..serializers import (
    TaskCreateSerializer,
    TaskReorderItemSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)
from activity_api.helpers import log_activity
from ._helpers import create_next_recurring_task, serialize_task
from ._notifications import _notify_assignments


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

    board, err = get_board_or_404(board_id, request.user)
    if err:
        return err

    if request.method == "GET":
        tasks = (
            board.tasks.filter(archived_at__isnull=True)
            .prefetch_related("subtasks", "attachments", "labels", "assignees", "dependencies__depends_on")
            .order_by("order", "created_at")[:500]
        )
        return Response([serialize_task(t) for t in tasks])

    if not can_edit_board(board, request.user):
        return Response({"detail": "You do not have permission to edit this board."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    column_id = data.get("column")
    if not column_id:
        first_column = board.columns.order_by("order").first()
        column_id = first_column.pk if first_column else None
    elif not Column.objects.filter(pk=column_id, board=board).exists():
        return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)

    assignee_ids = data.get("assigned_to", [])
    if assignee_ids:
        valid = Contact.objects.filter(pk__in=assignee_ids, owner=request.user).values_list("pk", flat=True)
        if len(set(assignee_ids)) != len(valid):
            return Response({"detail": "Invalid contact."}, status=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(
        board=board,
        title=data["title"],
        description=data.get("description", ""),
        priority=data.get("priority", Task.Priority.MEDIUM),
        column_id=column_id,
        due_date=data.get("due_date"),
        recurrence=data.get("recurrence"),
    )
    if assignee_ids:
        task.assignees.set(assignee_ids)
    _notify_assignments(task, set(), set(assignee_ids), request.user)
    log_activity(board, request.user, "created", "task", task.title)
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
        task = Task.objects.select_related("board").get(pk=pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_task(task))

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "You do not have permission to edit this board."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = TaskUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "assigned_to" in data:
            assignee_ids = data["assigned_to"]
            if assignee_ids:
                valid = Contact.objects.filter(pk__in=assignee_ids, owner=request.user).values_list("pk", flat=True)
                if len(set(assignee_ids)) != len(valid):
                    return Response({"detail": "Invalid contact."}, status=status.HTTP_400_BAD_REQUEST)
        if "column" in data and data["column"]:
            if not Column.objects.filter(pk=data["column"], board=task.board).exists():
                return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)
        previous_assignee_ids = set(task.assignees.values_list("pk", flat=True))
        previous_column_id = task.column_id
        changed_fields = []
        for field in ["title", "description", "priority", "column", "due_date", "recurrence", "order"]:
            key = f"{field}_id" if field == "column" else field
            if field in data:
                setattr(task, key, data[field])
                changed_fields.append(key)
        if changed_fields:
            task.save(update_fields=changed_fields)
        if "assigned_to" in data:
            new_assignee_ids = set(data["assigned_to"])
            task.assignees.set(new_assignee_ids)
            _notify_assignments(task, previous_assignee_ids, new_assignee_ids, request.user)
        if "label_ids" in data:
            task.labels.set(Label.objects.filter(pk__in=data["label_ids"], board=task.board))
        if task.column_id != previous_column_id:
            log_activity(task.board, request.user, "moved", "task", task.title)
        else:
            log_activity(task.board, request.user, "updated", "task", task.title)
        data = serialize_task(task)
        send_board_event(task.board_id, "task_updated", data)
        return Response(data)

    # Soft-delete: archive instead of destroying so tasks can be restored.
    task.archived_at = timezone.now()
    task.save(update_fields=["archived_at"])
    log_activity(task.board, request.user, "deleted", "task", task.title)
    send_board_event(task.board_id, "task_deleted", {"id": task.pk})

    # If task is recurring, archiving triggers creation of the next instance.
    new_task = create_next_recurring_task(task)
    if new_task:
        log_activity(task.board, request.user, "created", "task", new_task.title, "Recurring")
        send_board_event(task.board_id, "task_created", serialize_task(new_task))

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=TaskReorderItemSerializer(many=True),
    responses={204: None, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["POST"])
def task_reorder(request):
    serializer = TaskReorderItemSerializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    items = serializer.validated_data

    task_ids = [item["id"] for item in items]
    fetched = list(Task.objects.filter(pk__in=task_ids, archived_at__isnull=True).select_related("board"))
    if len(fetched) != len(set(task_ids)):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    for t in fetched:
        if not can_access_board(t.board, request.user):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
    tasks = {t.pk: t for t in fetched}

    board_ids = {t.board_id for t in fetched}
    columns_by_board = {}
    for col_id, bid in Column.objects.filter(board_id__in=board_ids).values_list("pk", "board_id"):
        columns_by_board.setdefault(bid, set()).add(col_id)

    for item in items:
        task = tasks.get(item.get("id"))
        if not task:
            continue
        if "order" in item:
            task.order = item["order"]
        if "column" in item:
            if item["column"] not in columns_by_board.get(task.board_id, set()):
                return Response({"detail": "Invalid column."}, status=status.HTTP_400_BAD_REQUEST)
            task.column_id = item["column"]

    with transaction.atomic():
        Task.objects.bulk_update(list(tasks.values()), ["order", "column_id"])

    board_ids = {t.board_id for t in tasks.values()}
    refreshed = {
        t.pk: t
        for t in Task.objects
        .filter(pk__in=tasks.keys())
        .prefetch_related("subtasks", "attachments", "labels", "assignees", "dependencies__depends_on")
    }
    for bid in board_ids:
        board_tasks = [serialize_task(refreshed[pk]) for pk in tasks if refreshed[pk].board_id == bid]
        send_board_event(bid, "tasks_reordered", board_tasks)

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={200: TaskSerializer(many=True)})
@api_view(["GET"])
def my_tasks(request):
    user = request.user
    boards = Board.objects.filter(Q(created_by=user) | Q(members__user=user)).distinct()
    tasks = (
        Task.objects.filter(board__in=boards, archived_at__isnull=True)
        .prefetch_related("subtasks", "attachments", "labels", "assignees", "dependencies__depends_on")
        .order_by("due_date", "created_at")[:1000]
    )
    return Response([serialize_task(t) for t in tasks])
