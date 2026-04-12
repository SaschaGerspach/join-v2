from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from .models import Column


def serialize_column(col):
    return {
        "id": col.pk,
        "board": col.board_id,
        "title": col.title,
        "order": col.order,
    }


@api_view(["GET", "POST"])
def column_list(request):
    board_id = request.query_params.get("board")

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        board = Board.objects.get(pk=board_id)
    except Board.DoesNotExist:
        return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        columns = board.columns.all().order_by("order")
        return Response([serialize_column(c) for c in columns])

    title = request.data.get("title", "").strip()
    if not title:
        return Response({"detail": "Title is required."}, status=status.HTTP_400_BAD_REQUEST)

    order = board.columns.count()
    column = Column.objects.create(board=board, title=title, order=order)
    return Response(serialize_column(column), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def column_detail(request, pk):
    try:
        column = Column.objects.get(pk=pk)
    except Column.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if column.board.created_by != request.user:
        return Response({"detail": "Only the board creator can modify columns."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        if "title" in request.data:
            column.title = request.data["title"].strip()
        if "order" in request.data:
            column.order = request.data["order"]
        column.save()
        return Response(serialize_column(column))

    column.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
