import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Board


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        if not await self._has_access(user, self.board_id):
            await self.close(code=4403)
            return

        self.group_name = f"board_{self.board_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def board_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _has_access(self, user, board_id):
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            return False
        return board.created_by_id == user.id or board.members.filter(user=user).exists()
