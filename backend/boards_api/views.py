from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Board, BoardMember

User = get_user_model()


class _BoardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


def _can_access(board, user):
    return board.created_by == user or board.members.filter(user=user).exists()


def serialize_board(board):
    return {
        "id": board.pk,
        "title": board.title,
        "color": board.color,
        "created_by": board.created_by_id,
        "created_at": board.created_at,
        "is_owner": True,
    }


def serialize_shared_board(board, user):
    return {
        "id": board.pk,
        "title": board.title,
        "color": board.color,
        "created_by": board.created_by_id,
        "created_at": board.created_at,
        "is_owner": board.created_by == user,
    }


@api_view(["GET", "POST"])
def board_list(request):
    if request.method == "GET":
        owned = Board.objects.filter(created_by=request.user)
        shared = Board.objects.filter(members__user=request.user)
        boards = (owned | shared).distinct().order_by("-created_at")
        paginator = _BoardPagination()
        page = paginator.paginate_queryset(boards, request)
        return paginator.get_paginated_response([serialize_shared_board(b, request.user) for b in page])

    title = request.data.get("title", "").strip()
    if not title:
        return Response({"detail": "Title is required."}, status=status.HTTP_400_BAD_REQUEST)

    board = Board.objects.create(title=title, created_by=request.user)
    return Response(serialize_board(board), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def board_detail(request, pk):
    try:
        board = Board.objects.get(pk=pk)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _can_access(board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_shared_board(board, request.user))

    if board.created_by != request.user:
        return Response({"detail": "Only the owner can modify this board."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        if "title" in request.data:
            board.title = request.data["title"].strip()
        if "color" in request.data:
            color = request.data["color"].strip()
            if len(color) == 7 and color.startswith("#"):
                board.color = color
        board.save()
        return Response(serialize_shared_board(board, request.user))

    board.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def board_members(request, pk):
    try:
        board = Board.objects.get(pk=pk, created_by=request.user)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        members = board.members.select_related("user").all()
        return Response([{
            "user_id": m.user_id,
            "email": m.user.email,
            "first_name": m.user.first_name,
            "last_name": m.user.last_name,
            "invited_at": m.invited_at,
        } for m in members])

    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    if email == request.user.email:
        return Response({"detail": "You cannot invite yourself."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invitee = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "No user found with that email."}, status=status.HTTP_404_NOT_FOUND)

    _, created = BoardMember.objects.get_or_create(board=board, user=invitee)
    if not created:
        return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)

    send_mail(
        subject=f"You've been invited to a board — Join",
        message=(
            f"{request.user.first_name or request.user.email} invited you to the board "
            f'"{board.title}" on Join.\n\n'
            f"Log in to access it: {settings.FRONTEND_URL}/boards/{board.pk}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitee.email],
        fail_silently=True,
    )

    return Response({
        "user_id": invitee.pk,
        "email": invitee.email,
        "first_name": invitee.first_name,
        "last_name": invitee.last_name,
    }, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def board_member_detail(request, pk, user_pk):
    try:
        board = Board.objects.get(pk=pk, created_by=request.user)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        member = BoardMember.objects.get(board=board, user_id=user_pk)
    except BoardMember.DoesNotExist:
        return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

    member.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
