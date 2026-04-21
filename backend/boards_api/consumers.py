import json
import logging
from collections import defaultdict

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

_board_presence: dict[str, dict[int, dict]] = defaultdict(dict)


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        self.group_name = None
        self.user = None
        await self.accept()

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

            user_info = {"id": user.pk, "first_name": user.first_name, "last_name": user.last_name, "email": user.email}
            _board_presence[self.group_name][user.pk] = user_info

            await self.send(text_data=json.dumps({"type": "authenticated"}))
            await self.send(text_data=json.dumps({"event": "presence_list", "data": list(_board_presence[self.group_name].values())}))

            await self.channel_layer.group_send(self.group_name, {
                "type": "board.event",
                "payload": {"event": "presence_joined", "data": user_info},
            })
            return

    async def disconnect(self, close_code):
        if self.group_name:
            if self.user:
                _board_presence[self.group_name].pop(self.user.pk, None)
                await self.channel_layer.group_send(self.group_name, {
                    "type": "board.event",
                    "payload": {"event": "presence_left", "data": {"id": self.user.pk}},
                })
                if not _board_presence[self.group_name]:
                    del _board_presence[self.group_name]
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def board_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

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
