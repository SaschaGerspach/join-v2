from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.permissions import can_access_board, can_edit_board
from boards_api.ws_events import send_board_event
from columns_api.models import Column
from config.serializers import DetailSerializer
from contacts_api.models import Contact
from ..models import Task
from ..serializers import TaskReorderItemSerializer, TaskSerializer
from activity_api.helpers import log_activity
from ..signals import task_created as task_created_signal, task_moved
from ._helpers import serialize_task


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

    with transaction.atomic():
        fetched = list(
            Task.objects.select_for_update()
            .filter(pk__in=task_ids, archived_at__isnull=True)
            .select_related("board")
        )
        if len(fetched) != len(set(task_ids)):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        for t in fetched:
            if not can_edit_board(t.board, request.user):
                return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        tasks = {t.pk: t for t in fetched}

        board_ids = {t.board_id for t in fetched}
        columns_by_board = {}
        for col_id, bid in Column.objects.filter(board_id__in=board_ids).values_list("pk", "board_id"):
            columns_by_board.setdefault(bid, set()).add(col_id)

        previous_columns = {t.pk: t.column_id for t in fetched}
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

    for pk, t in refreshed.items():
        if t.column_id != previous_columns.get(pk):
            task_moved.send(sender=Task, task=t, column_id=t.column_id)

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    parameters=[
        OpenApiParameter(name="search", type=str, required=False, location=OpenApiParameter.QUERY),
    ],
    responses={200: TaskSerializer(many=True)},
)
@api_view(["GET"])
def my_tasks(request):
    user = request.user
    boards = Board.objects.filter(Q(created_by=user) | Q(members__user=user) | Q(team__members__user=user) | Q(team__created_by=user)).distinct()
    qs = Task.objects.filter(board__in=boards, archived_at__isnull=True)

    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

    tasks = (
        qs.select_related("board")
        .prefetch_related("subtasks", "attachments", "labels", "assignees", "dependencies__depends_on")
        .order_by("due_date", "created_at")[:100]
    )
    return Response([{**serialize_task(t), "board_title": t.board.title} for t in tasks])


@extend_schema(responses={201: TaskSerializer, 404: DetailSerializer})
@api_view(["POST"])
def task_duplicate(request, pk):
    try:
        task = Task.objects.select_related("board").get(pk=pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    from ..models import Subtask
    new_task = Task.objects.create(
        board=task.board,
        column=task.column,
        title=f"{task.title} (copy)",
        description=task.description,
        priority=task.priority,
        start_date=task.start_date,
        due_date=task.due_date,
        recurrence=task.recurrence,
        order=task.order + 1,
    )
    new_task.assignees.set(task.assignees.all())
    new_task.labels.set(task.labels.all())
    for sub in task.subtasks.all():
        Subtask.objects.create(task=new_task, title=sub.title, done=False)

    log_activity(task.board, request.user, "created", "task", new_task.title, task=new_task)
    data = serialize_task(new_task)
    send_board_event(task.board_id, "task_created", data)
    task_created_signal.send(sender=Task, task=new_task)
    return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(responses={200: None, 404: DetailSerializer})
@api_view(["GET"])
def task_history(request, pk):
    try:
        task = Task.objects.select_related("board").get(pk=pk)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    entries = task.history.select_related("user").order_by("-created_at")[:50]
    result = []
    for entry in entries:
        user = entry.user
        user_name = f"{user.first_name} {user.last_name}".strip() or user.email if user else "Deleted user"
        result.append({
            "id": entry.pk,
            "user_name": user_name,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "details": entry.details,
            "created_at": entry.created_at,
        })
    return Response(result)


@extend_schema(responses={200: None})
@api_view(["GET"])
def task_workload(request):
    user = request.user
    boards = Board.objects.filter(
        Q(created_by=user) | Q(members__user=user) | Q(team__members__user=user) | Q(team__created_by=user)
    ).distinct()

    tasks = (
        Task.objects.filter(board__in=boards, archived_at__isnull=True)
        .select_related("board")
        .prefetch_related("assignees")
    )

    contacts_qs = Contact.objects.filter(owner=user)
    contacts = [{"id": c.pk, "name": f"{c.first_name} {c.last_name}".strip()} for c in contacts_qs]

    result = []
    for t in tasks:
        assignee_ids = [a.pk for a in t.assignees.all()]
        if not assignee_ids:
            continue
        result.append({
            "id": t.pk,
            "title": t.title,
            "priority": t.priority,
            "start_date": t.start_date,
            "due_date": t.due_date,
            "assigned_to": assignee_ids,
            "board_title": t.board.title,
        })

    return Response({"contacts": contacts, "tasks": result})
