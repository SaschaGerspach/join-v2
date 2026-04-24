import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health(request):
    from django.db import connection
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "error", "db": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health),
    path("admin-api/", include("admin_api.urls")),
    path("auth/", include("auth_api.urls")),
    path("users/", include("users_api.urls")),
    path("boards/", include("boards_api.urls")),
    path("columns/", include("columns_api.urls")),
    path("tasks/", include("tasks_api.urls")),
    path("contacts/", include("contacts_api.urls")),
    path("notifications/", include("notifications_api.urls")),
    path("activity/", include("activity_api.urls")),
    path("teams/", include("teams_api.urls")),
]

if settings.DEBUG or os.environ.get('DJANGO_ADMIN_ENABLED', 'false').lower() == 'true':
    urlpatterns += [path('manage/', admin.site.urls)]

if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
