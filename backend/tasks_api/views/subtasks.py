from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_access_board, can_edit_board
from config.serializers import DetailSerializer
from ..models import Task, Subtask
from ..serializers import (
    SubtaskCreateSerializer,
    SubtaskSerializer,
    SubtaskUpdateSerializer,
)


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
        task = Task.objects.select_related("board").get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_subtask(s) for s in task.subtasks.all()])

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = SubtaskCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    subtask = Subtask.objects.create(task=task, title=serializer.validated_data["title"])
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
        subtask = Subtask.objects.select_related("task__board").get(pk=pk, task_id=task_pk)
    except Subtask.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(subtask.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(subtask.task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = SubtaskUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "title" in data:
            subtask.title = data["title"]
        if "done" in data:
            subtask.done = data["done"]
        subtask.save()
        return Response(serialize_subtask(subtask))

    subtask.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
