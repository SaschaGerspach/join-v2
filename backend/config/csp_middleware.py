from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

_frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:4200')

_CSP_DIRECTIVES = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",
    "font-src": "'self'",
    "img-src": "'self' data: blob:",
    "media-src": "'self' blob:",
    "connect-src": f"'self' {_frontend_url}",
    "frame-src": "'self' blob:",
    "worker-src": "'self' blob:",
    "object-src": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'none'",
}

_s3_domain = os.environ.get('AWS_S3_CUSTOM_DOMAIN', '')
if not _s3_domain:
    _bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    if _bucket:
        _s3_domain = f"{_bucket}.s3.amazonaws.com"

if _s3_domain:
    _CSP_DIRECTIVES["img-src"] += f" https://{_s3_domain}"
    _CSP_DIRECTIVES["media-src"] += f" https://{_s3_domain}"
    _CSP_DIRECTIVES["connect-src"] += f" https://{_s3_domain}"

CSP_HEADER = "; ".join(f"{k} {v}" for k, v in _CSP_DIRECTIVES.items())


class CSPMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = CSP_HEADER
        return response
