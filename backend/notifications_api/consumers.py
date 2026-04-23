import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    AUTH_TIMEOUT = 10

    async def connect(self):
        self.group_name = None
        self.user = None
        await self.accept()
        self._auth_timer = asyncio.get_event_loop().call_later(self.AUTH_TIMEOUT, lambda: asyncio.ensure_future(self._auth_timeout()))

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
                await self.close(code=4401)
                return
            user = await self._authenticate(data["token"])
            if not user:
                await self.close(code=4401)
                return
            self.user = user
            self.group_name = f"user_{user.pk}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send(text_data=json.dumps({"type": "authenticated"}))
            return

    async def disconnect(self, close_code):
        if hasattr(self, '_auth_timer'):
            self._auth_timer.cancel()
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def user_notification(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _authenticate(self, token):
        try:
            validated = AccessToken(token)
            User = get_user_model()
            return User.objects.get(pk=validated["user_id"], is_active=True)
        except (TokenError, KeyError, User.DoesNotExist):
            return None
