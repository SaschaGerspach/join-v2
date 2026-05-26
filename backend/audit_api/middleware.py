from __future__ import annotations

from typing import TYPE_CHECKING

from .helpers import log_audit

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/auth/login/", "/auth/token/refresh/", "/auth/logout/"}


class AdminAuditMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if (
            request.method in WRITE_METHODS
            and hasattr(request, "user")
            and request.user.is_authenticated
            and request.user.is_staff
            and request.path not in SKIP_PATHS
            and 200 <= response.status_code < 400
        ):
            log_audit(
                "admin_action",
                user=request.user,
                request=request,
                detail=f"{request.method} {request.path}",
            )

        return response
