from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_access_board, can_edit_board
from ..models import Task, TaskDependency
from ..serializers import DependencySerializer, DependencyCreateSerializer


def _would_create_cycle(task, new_dependency):
    """Check if adding task→new_dependency would create a cycle (DFS from new_dependency back to task)."""
    visited = set()
    stack = [new_dependency.pk]
    while stack:
        current = stack.pop()
        if current == task.pk:
            return True
        if current in visited:
            continue
        visited.add(current)
        children = TaskDependency.objects.filter(task_id=current).values_list("depends_on_id", flat=True)
        stack.extend(children)
    return False


@extend_schema(
    methods=["GET"],
    responses={200: DependencySerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=DependencyCreateSerializer,
    responses={201: DependencySerializer},
)
@api_view(["GET", "POST"])
def dependency_list(request, task_pk):
    try:
        task = Task.objects.select_related("board").get(pk=task_pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        deps = task.dependencies.select_related("depends_on").all()
        data = [
            {"id": d.pk, "depends_on": d.depends_on_id, "title": d.depends_on.title}
            for d in deps
        ]
        return Response(data)

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = DependencyCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    depends_on_id = serializer.validated_data["depends_on"]

    if depends_on_id == task_pk:
        return Response({"detail": "A task cannot depend on itself."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target = Task.objects.select_related("board").get(pk=depends_on_id, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Target task not found."}, status=status.HTTP_404_NOT_FOUND)

    if target.board_id != task.board_id:
        return Response({"detail": "Tasks must be on the same board."}, status=status.HTTP_400_BAD_REQUEST)

    if _would_create_cycle(task, target):
        return Response({"detail": "Circular dependency."}, status=status.HTTP_400_BAD_REQUEST)

    dep, created = TaskDependency.objects.get_or_create(task=task, depends_on=target)
    data = {"id": dep.pk, "depends_on": target.pk, "title": target.title}
    return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@extend_schema(responses={204: None})
@api_view(["DELETE"])
def dependency_detail(request, task_pk, pk):
    try:
        task = Task.objects.select_related("board").get(pk=task_pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    deleted, _ = TaskDependency.objects.filter(pk=pk, task=task).delete()
    if not deleted:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_204_NO_CONTENT)
