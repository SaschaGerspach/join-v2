from django.db.models import Sum
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_access_board, can_edit_board
from ..models import Task, TimeEntry
from ..serializers import TimeEntryCreateSerializer, TimeEntrySerializer


def _serialize_entry(entry):
    name = f"{entry.user.first_name} {entry.user.last_name}".strip() or entry.user.email
    return {
        "id": entry.pk,
        "user_id": entry.user_id,
        "user_name": name,
        "duration_minutes": entry.duration_minutes,
        "note": entry.note,
        "logged_at": entry.logged_at,
    }


@extend_schema(
    methods=["GET"],
    responses={200: TimeEntrySerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=TimeEntryCreateSerializer,
    responses={201: TimeEntrySerializer},
)
@api_view(["GET", "POST"])
def time_entry_list(request, task_pk):
    try:
        task = Task.objects.select_related("board").get(pk=task_pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        entries = task.time_entries.select_related("user").all()
        total = entries.aggregate(total=Sum("duration_minutes"))["total"] or 0
        return Response({
            "total_minutes": total,
            "entries": [_serialize_entry(e) for e in entries],
        })

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TimeEntryCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entry = TimeEntry.objects.create(
        task=task,
        user=request.user,
        duration_minutes=serializer.validated_data["duration_minutes"],
        note=serializer.validated_data.get("note", ""),
    )
    entry.user = request.user
    return Response(_serialize_entry(entry), status=status.HTTP_201_CREATED)


@extend_schema(responses={204: None})
@api_view(["DELETE"])
def time_entry_detail(request, task_pk, pk):
    try:
        task = Task.objects.select_related("board").get(pk=task_pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        entry = TimeEntry.objects.get(pk=pk, task=task)
    except TimeEntry.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if entry.user_id != request.user.id and not request.user.is_staff:
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    entry.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
