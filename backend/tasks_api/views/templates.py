from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_edit_board, get_board_or_404
from config.serializers import DetailSerializer
from ..models import TaskTemplate, Task, Subtask, Label
from ..serializers import TaskTemplateSerializer, TaskTemplateUpdateSerializer, TaskSerializer
from ..signals import task_created as task_created_signal
from activity_api.helpers import log_activity
from boards_api.ws_events import send_board_event
from ._helpers import serialize_task


@extend_schema(
    methods=["GET"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: TaskTemplateSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    request=TaskTemplateSerializer,
    responses={201: TaskTemplateSerializer, 400: DetailSerializer},
)
@api_view(["GET", "POST"])
def template_list(request):
    board_id = request.query_params.get("board")
    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    board, err = get_board_or_404(board_id, request.user)
    if err:
        return err

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        templates = board.task_templates.all()
        return Response(TaskTemplateSerializer(templates, many=True).data)

    serializer = TaskTemplateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    template = TaskTemplate.objects.create(
        board=board,
        name=data["name"],
        title=data.get("title", ""),
        description=data.get("description", ""),
        priority=data.get("priority", "medium"),
        subtasks=data.get("subtasks", []),
        label_ids=data.get("label_ids", []),
    )
    return Response(TaskTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=TaskTemplateUpdateSerializer,
    responses={200: TaskTemplateSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def template_detail(request, pk):
    try:
        template = TaskTemplate.objects.select_related("board").get(pk=pk)
    except TaskTemplate.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(template.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = TaskTemplateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    for field in ["name", "title", "description", "priority", "subtasks", "label_ids"]:
        if field in data:
            setattr(template, field, data[field])
    template.save()
    return Response(TaskTemplateSerializer(template).data)


@extend_schema(
    responses={201: TaskSerializer, 404: DetailSerializer},
)
@api_view(["POST"])
def template_create_task(request, pk):
    try:
        template = TaskTemplate.objects.select_related("board").get(pk=pk)
    except TaskTemplate.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    board = template.board
    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    first_column = board.columns.order_by("order").first()

    task = Task.objects.create(
        board=board,
        column=first_column,
        title=template.title or template.name,
        description=template.description,
        priority=template.priority or Task.Priority.MEDIUM,
    )

    if template.subtasks:
        for sub_title in template.subtasks:
            Subtask.objects.create(task=task, title=sub_title)

    if template.label_ids:
        labels = Label.objects.filter(pk__in=template.label_ids, board=board)
        task.labels.set(labels)

    log_activity(board, request.user, "created", "task", task.title, task=task)
    data = serialize_task(task)
    send_board_event(board.pk, "task_created", data)
    task_created_signal.send(sender=Task, task=task)
    return Response(data, status=status.HTTP_201_CREATED)
