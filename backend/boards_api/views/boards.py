from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from columns_api.models import Column
from config.serializers import DetailSerializer
from ..models import Board
from ..permissions import can_access_board
from ..serializers import (
    BoardCreateSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
)


class _BoardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


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


@extend_schema(
    methods=["GET"],
    responses={200: BoardSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=BoardCreateSerializer,
    responses={201: BoardSerializer, 400: DetailSerializer},
)
@api_view(["GET", "POST"])
def board_list(request):
    if request.method == "GET":
        owned = Board.objects.filter(created_by=request.user)
        shared = Board.objects.filter(members__user=request.user)
        boards = (owned | shared).distinct().order_by("-created_at")
        paginator = _BoardPagination()
        page = paginator.paginate_queryset(boards, request)
        return paginator.get_paginated_response([serialize_shared_board(b, request.user) for b in page])

    serializer = BoardCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    board = Board.objects.create(title=serializer.validated_data["title"], created_by=request.user)
    Column.objects.bulk_create([
        Column(board=board, title=t, order=i) for i, t in enumerate(settings.DEFAULT_BOARD_COLUMNS)
    ])
    return Response(serialize_board(board), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    responses={200: BoardSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=BoardUpdateSerializer,
    responses={200: BoardSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "PATCH", "DELETE"])
def board_detail(request, pk):
    try:
        board = Board.objects.get(pk=pk)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_shared_board(board, request.user))

    if board.created_by != request.user:
        return Response({"detail": "Only the owner can modify this board."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = BoardUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "title" in data:
            board.title = data["title"]
        if "color" in data:
            board.color = data["color"]
        board.save()
        return Response(serialize_shared_board(board, request.user))

    board.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
