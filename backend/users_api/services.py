from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from boards_api.models import Board, BoardMember
from teams_api.models import Team, TeamMember

if TYPE_CHECKING:
    from auth_api.models import User

logger = logging.getLogger(__name__)


def revoke_all_refresh_tokens(user: User) -> None:
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def delete_account(user: User) -> None:
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
                successor.delete()
            else:
                board.title = f"[Deleted User] {board.title}"
                board.save(update_fields=["title"])
        BoardMember.objects.filter(user=user).delete()

        for team in Team.objects.select_for_update().filter(created_by=user):
            successor = TeamMember.objects.filter(team=team).order_by("joined_at").first()
            if successor:
                team.created_by = successor.user
                team.save(update_fields=["created_by"])
                successor.delete()
            else:
                team.delete()
        TeamMember.objects.filter(user=user).delete()

        anon_id = uuid.uuid4().hex[:8]
        user.email = f"deleted-{anon_id}@anonymized.local"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.is_active = False
        user.set_unusable_password()
        user.totp_secret = ""
        if user.avatar:
            try:
                user.avatar.delete(save=False)
            except Exception:
                logger.warning("Failed to delete avatar file for user %s", user.pk)
        user.save()

    revoke_all_refresh_tokens(user)
