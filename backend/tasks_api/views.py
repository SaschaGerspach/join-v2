from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from .models import Task, Subtask


def serialize_task(task):
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

    if request.method == "GET":
        tasks = board.tasks.all().order_by("created_at")
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
    return Response(serialize_task(task), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_task(task))

    if task.board.created_by != request.user:
        return Response({"detail": "Only the board creator can modify tasks."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        for field in ["title", "description", "priority", "column", "assigned_to", "due_date"]:
            key = field if field not in ["column", "assigned_to"] else f"{field}_id"
            data_key = field
            if data_key in request.data:
                setattr(task, key, request.data[data_key])
        task.save()
        return Response(serialize_task(task))

    task.delete()
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

    if subtask.task.board.created_by != request.user:
        return Response({"detail": "Only the board creator can modify subtasks."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        if "title" in request.data:
            subtask.title = request.data["title"].strip()
        if "done" in request.data:
            subtask.done = request.data["done"]
        subtask.save()
        return Response(serialize_subtask(subtask))

    subtask.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
