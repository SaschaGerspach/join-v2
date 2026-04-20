import re
import uuid

from django.http import FileResponse
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_access_board
from boards_api.ws_events import send_board_event
from config.serializers import DetailSerializer
from ..models import Task, Attachment
from ..serializers import AttachmentSerializer, AttachmentUploadSerializer
from ._helpers import ALLOWED_ATTACHMENT_EXTENSIONS, serialize_task


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
        task = Task.objects.select_related("board").get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
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
        att = Attachment.objects.select_related("task__board").get(pk=pk, task_id=task_pk)
    except Attachment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(att.task.board, request.user):
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

    if not can_access_board(att.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        return FileResponse(att.file.open("rb"), as_attachment=True, filename=att.filename)
    except (FileNotFoundError, OSError):
        return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
