from __future__ import annotations

import logging

import pyotp
from cryptography.fernet import InvalidToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from ..encryption import decrypt_totp_secret

User = get_user_model()
logger = logging.getLogger(__name__)


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


def verify_totp_code(user: User, code: str) -> bool:
    try:
        secret = decrypt_totp_secret(user.totp_secret)
    except InvalidToken:
        logger.error("Cannot decrypt TOTP secret for user %s; was TOTP_ENCRYPTION_KEY changed?", user.pk)
        return False
    totp = pyotp.TOTP(secret)
    now = timezone.now()
    if not totp.verify(code, for_time=now):
        return False
    counter = totp.timecode(now)
    # Conditional update so a code is accepted at most once, even for concurrent requests.
    consumed = (
        User.objects.filter(pk=user.pk)
        .filter(Q(totp_last_counter__isnull=True) | Q(totp_last_counter__lt=counter))
        .update(totp_last_counter=counter)
    )
    return consumed == 1


def issue_tokens_for(user: User) -> tuple[RefreshToken, AccessToken]:
    refresh = RefreshToken.for_user(user)
    return refresh, refresh.access_token
