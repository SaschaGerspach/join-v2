import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


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
                await self.close(code=4401)
                return
            user = await self._authenticate(data["token"])
            if not user or not await self._has_access(user, self.board_id):
                await self.close(code=4401)
                return
            self.user = user
            self.group_name = f"board_{self.board_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send(text_data=json.dumps({"type": "authenticated"}))
            return

    async def disconnect(self, close_code):
        if self.group_name:
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
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            return False
        return board.created_by_id == user.id or board.members.filter(user=user).exists()
