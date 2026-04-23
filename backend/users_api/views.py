import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenClass

from auth_api.views._helpers import clear_refresh_cookie
from boards_api.models import Board, BoardMember
from config.serializers import DetailSerializer
from audit_api.helpers import log_audit
from .serializers import PublicUserSerializer, UserUpdateSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


def _co_member_ids(user):
    shared_boards = Board.objects.filter(
        Q(created_by=user) | Q(members__user=user)
    )
    return (
        User.objects.filter(
            Q(boards__in=shared_boards) | Q(board_memberships__board__in=shared_boards)
        )
        .exclude(pk=user.pk)
        .values_list("pk", flat=True)
        .distinct()
    )


class _UserPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


def serialize_user(user):
    return {
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@extend_schema(responses={200: PublicUserSerializer(many=True)})
@api_view(["GET"])
def user_list(request):
    allowed_ids = _co_member_ids(request.user)
    users = User.objects.filter(pk__in=allowed_ids, is_active=True).order_by("id")
    paginator = _UserPagination()
    page = paginator.paginate_queryset(users, request)
    return paginator.get_paginated_response([serialize_user(u) for u in page])


@extend_schema(
    methods=["GET"],
    responses={200: PublicUserSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=UserUpdateSerializer,
    responses={200: PublicUserSerializer, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "PATCH", "DELETE"])
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        if user.pk != request.user.pk and user.pk not in set(_co_member_ids(request.user)):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_user(user))

    if request.method == "PATCH":
        if request.user.pk != pk and not request.user.is_staff:
            return Response({"detail": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "email" in data and not request.user.is_staff:
            return Response({"detail": "Only admins can change email addresses."}, status=status.HTTP_403_FORBIDDEN)
        if "email" in data:
            new_email = data["email"].lower()
            if User.objects.filter(email=new_email, is_active=True).exclude(pk=pk).exists():
                return Response({"detail": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        for field in ["first_name", "last_name", "email"]:
            if field in data:
                value = data[field]
                if field == "email":
                    value = value.lower()
                setattr(user, field, value)
        if "password" in data:
            user.set_password(data["password"])
        user.save()
        return Response(serialize_user(user))

    if request.method == "DELETE":
        if not request.user.is_staff:
            return Response({"detail": "Only admins can delete accounts."}, status=status.HTTP_403_FORBIDDEN)

        # Transfer ownership to the longest-standing member; if no members exist, delete the board entirely.
        with transaction.atomic():
            for board in Board.objects.select_for_update().filter(created_by=user):
                successor = (
                    BoardMember.objects.select_for_update()
                    .filter(board=board)
                    .order_by("invited_at")
                    .first()
                )
                if successor:
                    board.created_by = successor.user
                    board.save(update_fields=["created_by"])
                    # Remove membership row since the successor is now the owner (implicit role).
                    successor.delete()
                else:
                    board.title = f"[Deleted User] {board.title}"
                    board.save(update_fields=["title"])
            BoardMember.objects.filter(user=user).delete()
            user.is_active = False
            user.save(update_fields=["is_active"])
        log_audit("account_deleted", user=user, request=request, detail=f"email={user.email}")

        for token in OutstandingToken.objects.filter(user=user):
            try:
                RefreshTokenClass(token.token).blacklist()
            except Exception:
                logger.warning("Failed to blacklist token %s for user %s", token.pk, user.pk)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


@extend_schema(responses={200: None})
@api_view(["GET"])
def data_export(request):
    user = request.user
    from tasks_api.models import Task, Comment
    from contacts_api.models import Contact
    from notifications_api.models import Notification

    boards = list(Board.objects.filter(Q(created_by=user) | Q(members__user=user)).distinct().values(
        "id", "title", "color", "created_at"
    ))
    tasks = list(Task.objects.filter(board__in=[b["id"] for b in boards]).values(
        "id", "board_id", "title", "description", "priority", "due_date", "created_at"
    ))
    comments = list(Comment.objects.filter(author=user).values(
        "id", "task_id", "text", "created_at"
    ))
    contacts = list(Contact.objects.filter(owner=user).values(
        "id", "first_name", "last_name", "email", "phone"
    ))
    notifications = list(Notification.objects.filter(recipient=user).order_by("-created_at")[:200].values(
        "id", "type", "message", "is_read", "created_at"
    ))

    data = {
        "user": {
            "id": user.pk,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
        },
        "boards": boards,
        "tasks": tasks,
        "comments": comments,
        "contacts": contacts,
        "notifications": notifications,
    }
    return Response(data)
