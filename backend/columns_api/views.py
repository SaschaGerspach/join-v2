from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.db.models import Q

from activity_api.helpers import log_activity
from boards_api.models import Board
from boards_api.permissions import can_access_board, can_edit_board, get_board_or_404
from boards_api.ws_events import send_board_event
from config.serializers import DetailSerializer
from .models import Column
from .serializers import (
    ColumnCreateSerializer,
    ColumnReorderItemSerializer,
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

    if request.method == "GET" and not board_id:
        user = request.user
        boards = Board.objects.filter(
            Q(created_by=user) | Q(members__user=user) | Q(team__members__user=user) | Q(team__created_by=user)
        ).distinct()
        columns = Column.objects.filter(board__in=boards).order_by("board_id", "order")
        return Response([serialize_column(c) for c in columns])

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    board, err = get_board_or_404(board_id, request.user)
    if err:
        return err

    if request.method == "GET":
        columns = board.columns.all().order_by("order")
        return Response([serialize_column(c) for c in columns])

    if not can_edit_board(board, request.user):
        return Response({"detail": "You do not have permission to create columns."}, status=status.HTTP_403_FORBIDDEN)

    serializer = ColumnCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    order = board.columns.count()
    column = Column.objects.create(board=board, title=serializer.validated_data["title"], order=order)
    log_activity(board, request.user, "created", "column", column.title)
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
        column = Column.objects.select_related("board").get(pk=pk)
    except Column.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(column.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(column.board, request.user):
        return Response({"detail": "You do not have permission to modify columns."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = ColumnUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        changed_fields = []
        if "title" in data:
            column.title = data["title"]
            changed_fields.append("title")
        if "order" in data:
            column.order = data["order"]
            changed_fields.append("order")
        if "wip_limit" in data:
            column.wip_limit = data["wip_limit"]
            changed_fields.append("wip_limit")
        if changed_fields:
            column.save(update_fields=changed_fields)
        log_activity(column.board, request.user, "updated", "column", column.title)
        data = serialize_column(column)
        send_board_event(column.board_id, "column_updated", data)
        return Response(data)

    board_id = column.board_id
    col_id = column.pk
    col_title = column.title
    board = column.board
    column.delete()
    log_activity(board, request.user, "deleted", "column", col_title)
    send_board_event(board_id, "column_deleted", {"id": col_id})
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=ColumnReorderItemSerializer(many=True),
    responses={200: ColumnSerializer(many=True), 400: DetailSerializer},
)
@api_view(["POST"])
def column_reorder(request):
    serializer = ColumnReorderItemSerializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    items = serializer.validated_data
    col_ids = [item["id"] for item in items]
    columns = Column.objects.select_related("board").filter(pk__in=col_ids)
    col_map = {c.pk: c for c in columns}

    if len(col_map) != len(col_ids):
        return Response({"detail": "Some columns not found."}, status=status.HTTP_400_BAD_REQUEST)

    boards = {c.board for c in col_map.values()}
    if len(boards) != 1:
        return Response({"detail": "All columns must belong to the same board."}, status=status.HTTP_400_BAD_REQUEST)

    board = boards.pop()
    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    for item in items:
        col = col_map[item["id"]]
        col.order = item["order"]
    Column.objects.bulk_update(col_map.values(), ["order"])

    result = [serialize_column(col_map[item["id"]]) for item in items]
    send_board_event(board.pk, "columns_reordered", result)
    return Response(result)
