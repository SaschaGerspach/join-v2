from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from activity_api.helpers import log_activity
from boards_api.models import Board
from boards_api.permissions import can_access_board, is_board_owner
from boards_api.ws_events import send_board_event
from config.serializers import DetailSerializer
from ..models import Task
from ..serializers import TaskSerializer
from ._helpers import serialize_task


@extend_schema(
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: TaskSerializer(many=True), 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET"])
def task_archive(request):
    board_id = request.query_params.get("board")

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        board = Board.objects.get(pk=board_id)
    except Board.DoesNotExist:
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(board, request.user):
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if not is_board_owner(board, request.user):
        return Response({"detail": "Only the board owner or an admin can view the archive."}, status=status.HTTP_403_FORBIDDEN)

    tasks = (
        board.tasks.filter(archived_at__isnull=False)
        .prefetch_related("subtasks", "attachments", "labels", "assignees")
        .order_by("-archived_at")
    )
    return Response([serialize_task(t) for t in tasks])


@extend_schema(
    responses={200: TaskSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["POST"])
def task_restore(request, pk):
    try:
        task = Task.objects.get(pk=pk, archived_at__isnull=False)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not is_board_owner(task.board, request.user):
        return Response({"detail": "Only the board owner or an admin can restore tasks."}, status=status.HTTP_403_FORBIDDEN)

    task.archived_at = None
    task.save(update_fields=["archived_at"])
    log_activity(task.board, request.user, "updated", "task", task.title, "Restored from archive")
    data = serialize_task(task)
    send_board_event(task.board_id, "task_created", data)
    return Response(data)
