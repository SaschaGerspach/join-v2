from .helpers import log_audit

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/auth/login/", "/auth/token/refresh/", "/auth/logout/"}


class AdminAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
