from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response

from auth_api.models import User
from teams_api.models import TeamMember
from .models import Board, BoardMember

_NOT_FOUND = {"detail": "Board not found."}


def _get_member_role(board: Board, user: User) -> str | None:
    try:
        return board.members.get(user=user).role
    except BoardMember.DoesNotExist:
        return None


# Board owner (created_by) has implicit full control — not stored as a BoardMember role.
def can_access_board(board: Board, user: User) -> bool:
    if user.is_staff:
        return True
    if board.created_by_id == user.id or board.members.filter(user=user).exists():
        return True
    if board.team_id and TeamMember.objects.filter(team_id=board.team_id, user=user).exists():
        return True
    return False


def can_edit_board(board: Board, user: User) -> bool:
    if user.is_staff or board.created_by_id == user.id:
        return True
    role = _get_member_role(board, user)
    if role in (BoardMember.Role.ADMIN, BoardMember.Role.EDITOR):
        return True
    if board.team_id and TeamMember.objects.filter(team_id=board.team_id, user=user).exists():
        return True
    return False


def can_manage_members(board: Board, user: User) -> bool:
    if user.is_staff or board.created_by_id == user.id:
        return True
    role = _get_member_role(board, user)
    return role == BoardMember.Role.ADMIN


def is_board_owner(board: Board, user: User) -> bool:
    if user.is_staff:
        return True
    return board.created_by_id == user.id


def get_board_or_404(pk: int | str, user: User) -> tuple[Board | None, Response | None]:
    try:
        board = Board.objects.get(pk=int(pk))
    except (Board.DoesNotExist, ValueError, TypeError):
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    if not can_access_board(board, user):
        return None, Response(_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    return board, None
