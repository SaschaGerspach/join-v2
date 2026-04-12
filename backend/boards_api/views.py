from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Board


class _BoardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


def serialize_board(board):
    return {
        "id": board.pk,
        "title": board.title,
        "created_by": board.created_by_id,
        "created_at": board.created_at,
    }


@api_view(["GET", "POST"])
def board_list(request):
    if request.method == "GET":
        boards = Board.objects.filter(created_by=request.user).order_by("-created_at")
        paginator = _BoardPagination()
        page = paginator.paginate_queryset(boards, request)
        return paginator.get_paginated_response([serialize_board(b) for b in page])

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

    if board.created_by != request.user:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_board(board))

    if request.method == "PATCH":
        if "title" in request.data:
            board.title = request.data["title"].strip()
            board.save()
        return Response(serialize_board(board))

    if request.method == "DELETE":
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
