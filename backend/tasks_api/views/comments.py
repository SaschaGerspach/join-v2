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


def serialize_comment(comment, request=None):
    avatar_url = None
    if comment.author.avatar:
        avatar_url = request.build_absolute_uri(comment.author.avatar.url) if request else comment.author.avatar.url
    return {
        "id": comment.pk,
        "task": comment.task_id,
        "author_id": comment.author_id,
        "author_name": f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.email,
        "author_avatar_url": avatar_url,
        "parent_id": comment.parent_id,
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
        return Response([serialize_comment(c, request) for c in task.comments.select_related("author").all()])

    serializer = CommentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    parent_id = serializer.validated_data.get("parent_id")
    parent = None
    if parent_id:
        parent = Comment.objects.filter(pk=parent_id, task=task).first()
    comment = Comment.objects.create(task=task, author=request.user, text=serializer.validated_data["text"], parent=parent)
    _notify_comment(comment, request.user)
    _notify_mentions(comment, request.user)
    log_activity(task.board, request.user, "created", "comment", task.title, task=task)
    return Response(serialize_comment(comment, request), status=status.HTTP_201_CREATED)


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
        return Response(serialize_comment(comment, request))

    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
