from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_access_board
from ..models import Task, TaskWatcher


@api_view(["GET", "POST", "DELETE"])
def task_watch(request, pk):
    try:
        task = Task.objects.select_related("board").get(pk=pk)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        is_watching = TaskWatcher.objects.filter(task=task, user=request.user).exists()
        watcher_count = task.watchers.count()
        return Response({"is_watching": is_watching, "watcher_count": watcher_count})

    if request.method == "POST":
        TaskWatcher.objects.get_or_create(task=task, user=request.user)
        return Response({"is_watching": True, "watcher_count": task.watchers.count()}, status=status.HTTP_201_CREATED)

    TaskWatcher.objects.filter(task=task, user=request.user).delete()
    return Response({"is_watching": False, "watcher_count": task.watchers.count()})
