from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from activity_api.helpers import log_activity
from boards_api.permissions import can_access_board
from config.serializers import DetailSerializer
from ..models import Task, Comment
from ..serializers import CommentCreateSerializer, CommentSerializer
from ._notifications import _notify_comment, _notify_mentions


def serialize_comment(comment):
    return {
        "id": comment.pk,
        "task": comment.task_id,
        "author_id": comment.author_id,
        "author_name": f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.email,
        "text": comment.text,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@extend_schema(
    methods=["GET"],
    responses={200: CommentSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=CommentCreateSerializer,
    responses={201: CommentSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "POST"])
def comment_list(request, task_pk):
    try:
        task = Task.objects.select_related("board__created_by").get(pk=task_pk)
    except Task.DoesNotExist:
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_comment(c) for c in task.comments.select_related("author").all()])

    serializer = CommentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    comment = Comment.objects.create(task=task, author=request.user, text=serializer.validated_data["text"])
    _notify_comment(comment, request.user)
    _notify_mentions(comment, request.user)
    log_activity(task.board, request.user, "created", "comment", task.title)
    return Response(serialize_comment(comment), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=CommentCreateSerializer,
    responses={200: CommentSerializer, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def comment_detail(request, task_pk, pk):
    try:
        comment = Comment.objects.select_related("author", "task__board").get(pk=pk, task_id=task_pk)
    except Comment.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(comment.task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if comment.author != request.user and not request.user.is_staff:
        return Response({"detail": "You can only edit your own comments."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        comment.text = serializer.validated_data["text"]
        comment.save(update_fields=["text", "updated_at"])
        return Response(serialize_comment(comment))

    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
