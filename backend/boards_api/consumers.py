from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

_PRESENCE_TTL = 300


def _presence_key(group_name: str) -> str:
    return f"presence:{group_name}"


class BoardConsumer(AsyncWebsocketConsumer):
    AUTH_TIMEOUT = 10

    async def connect(self):
        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        self.group_name = None
        self.user = None
        await self.accept()
        self._auth_timer = asyncio.get_running_loop().call_later(self.AUTH_TIMEOUT, lambda: asyncio.ensure_future(self._auth_timeout()))

    async def _auth_timeout(self):
        if self.user is None:
            await self.close(code=4408)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        if self.user is None:
            if data.get("type") != "authenticate" or not data.get("token"):
                logger.warning("WebSocket auth missing token for board %s", self.board_id)
                await self.close(code=4401)
                return
            user = await self._authenticate(data["token"])
            if not user or not await self._has_access(user, self.board_id):
                logger.warning("WebSocket auth failed for board %s", self.board_id)
                await self.close(code=4401)
                return
            self.user = user
            self.group_name = f"board_{self.board_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

            user_info = {"id": user.pk, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "avatar_url": user.avatar.url if user.avatar else None}
            presence_list = await self._add_presence(user.pk, user_info)

            await self.send(text_data=json.dumps({"type": "authenticated"}))
            await self.send(text_data=json.dumps({"event": "presence_list", "data": presence_list}))

            await self.channel_layer.group_send(self.group_name, {
                "type": "board.event",
                "payload": {"event": "presence_joined", "data": user_info},
            })
            return

    async def disconnect(self, close_code):
        if hasattr(self, '_auth_timer'):
            self._auth_timer.cancel()
        if self.group_name:
            if self.user:
                await self._remove_presence(self.user.pk)
                await self.channel_layer.group_send(self.group_name, {
                    "type": "board.event",
                    "payload": {"event": "presence_left", "data": {"id": self.user.pk}},
                })
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def board_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _add_presence(self, user_pk: int, user_info: dict[str, Any]) -> list[dict[str, Any]]:
        key = _presence_key(self.group_name)
        data = cache.get(key) or {}
        data[user_pk] = user_info
        cache.set(key, data, _PRESENCE_TTL)
        return list(data.values())

    @database_sync_to_async
    def _remove_presence(self, user_pk: int) -> None:
        key = _presence_key(self.group_name)
        data = cache.get(key) or {}
        data.pop(user_pk, None)
        if data:
            cache.set(key, data, _PRESENCE_TTL)
        else:
            cache.delete(key)

    @database_sync_to_async
    def _authenticate(self, token):
        try:
            validated = AccessToken(token)
            User = get_user_model()
            return User.objects.get(pk=validated["user_id"], is_active=True)
        except (TokenError, KeyError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def _has_access(self, user, board_id):
        from .models import Board
        from .permissions import can_access_board
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            return False
        return can_access_board(board, user)
