from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

User = get_user_model()


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth_attempts"


def set_refresh_cookie(response: Response, token: RefreshToken | str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=str(token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None),
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None),
    )


def issue_tokens_for(user: User) -> tuple[RefreshToken, AccessToken]:
    refresh = RefreshToken.for_user(user)
    return refresh, refresh.access_token
