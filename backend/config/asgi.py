import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi = get_asgi_application()

from boards_api.routing import websocket_urlpatterns as board_ws  # noqa: E402
from notifications_api.routing import websocket_urlpatterns as notification_ws  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": OriginValidator(
        URLRouter(board_ws + notification_ws),
        settings.CORS_ALLOWED_ORIGINS,
    ),
})
