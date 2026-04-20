from rest_framework import status
from rest_framework.response import Response

from .models import Board, BoardMember

_NOT_FOUND = {"detail": "Board not found."}


def _get_member_role(board, user):
    try:
        return board.members.get(user=user).role
    except BoardMember.DoesNotExist:
        return None


# Board owner (created_by) has implicit full control — not stored as a BoardMember role.
def can_access_board(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id or board.members.filter(user=user).exists()


def can_edit_board(board, user):
    if user.is_staff or board.created_by_id == user.id:
        return True
    role = _get_member_role(board, user)
    return role in (BoardMember.Role.ADMIN, BoardMember.Role.EDITOR)


def can_manage_members(board, user):
    if user.is_staff or board.created_by_id == user.id:
        return True
    role = _get_member_role(board, user)
    return role == BoardMember.Role.ADMIN


def is_board_owner(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id


def get_board_or_404(pk, user):
    try:
        board = Board.objects.get(pk=int(pk))
    except (Board.DoesNotExist, ValueError, TypeError):
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    if not can_access_board(board, user):
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    return board, None
