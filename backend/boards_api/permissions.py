from rest_framework import status
from rest_framework.response import Response

from .models import Board

_NOT_FOUND = {"detail": "Board not found."}


def can_access_board(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id or board.members.filter(user=user).exists()


def is_board_owner(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id


def get_board_or_404(pk, user):
    try:
        board = Board.objects.get(pk=pk)
    except Board.DoesNotExist:
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    if not can_access_board(board, user):
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    return board, None
