from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

from .models import AuditLog

if TYPE_CHECKING:
    from django.http import HttpRequest

    from auth_api.models import User

TRUSTED_PROXY_COUNT: int = getattr(settings, "TRUSTED_PROXY_COUNT", 1)


def get_client_ip(request: HttpRequest) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        parts = [p.strip() for p in xff.split(",")]
        try:
            return parts[-TRUSTED_PROXY_COUNT]
        except IndexError:
            return parts[0]
    return request.META.get("REMOTE_ADDR")


MAX_DETAIL_LENGTH = 1000


def log_audit(
    event_type: str,
    *,
    user: User | None = None,
    request: HttpRequest | None = None,
    detail: str = "",
) -> None:
    AuditLog.objects.create(
        user=user,
        event_type=event_type,
        detail=detail[:MAX_DETAIL_LENGTH] if detail else "",
        ip_address=get_client_ip(request) if request else None,
    )
