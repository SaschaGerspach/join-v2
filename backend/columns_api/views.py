from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.permissions import can_access_board, is_board_owner
from boards_api.ws_events import send_board_event
from config.serializers import DetailSerializer
from .models import Column
from .serializers import (
    ColumnCreateSerializer,
    ColumnSerializer,
    ColumnUpdateSerializer,
)


def serialize_column(col):
    return {
        "id": col.pk,
        "board": col.board_id,
        "title": col.title,
        "order": col.order,
        "wip_limit": col.wip_limit,
    }


@extend_schema(
    methods=["GET"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: ColumnSerializer(many=True), 400: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    request=ColumnCreateSerializer,
    responses={201: ColumnSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "POST"])
def column_list(request):
    board_id = request.query_params.get("board")

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        board = Board.objects.get(pk=board_id)
    except Board.DoesNotExist:
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(board, request.user):
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        columns = board.columns.all().order_by("order")
        return Response([serialize_column(c) for c in columns])

    if not is_board_owner(board, request.user):
        return Response({"detail": "Only the board owner can create columns."}, status=status.HTTP_403_FORBIDDEN)

    serializer = ColumnCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    order = board.columns.count()
    column = Column.objects.create(board=board, title=serializer.validated_data["title"], order=order)
    data = serialize_column(column)
    send_board_event(board.pk, "column_created", data)
    return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=ColumnUpdateSerializer,
    responses={200: ColumnSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def column_detail(request, pk):
    try:
        column = Column.objects.get(pk=pk)
    except Column.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(column.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not is_board_owner(column.board, request.user):
        return Response({"detail": "Only the board owner can modify columns."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = ColumnUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "title" in data:
            column.title = data["title"]
        if "order" in data:
            column.order = data["order"]
        if "wip_limit" in data:
            column.wip_limit = data["wip_limit"]
        column.save()
        data = serialize_column(column)
        send_board_event(column.board_id, "column_updated", data)
        return Response(data)

    board_id = column.board_id
    col_id = column.pk
    column.delete()
    send_board_event(board_id, "column_deleted", {"id": col_id})
    return Response(status=status.HTTP_204_NO_CONTENT)
