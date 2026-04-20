"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from config.serializers import AdminStatsSerializer

from boards_api.models import Board
from tasks_api.models import Task
from contacts_api.models import Contact


def health(request):
    return JsonResponse({"status": "ok"})


class _AdminThrottle(UserRateThrottle):
    rate = "30/minute"


@extend_schema(responses={200: AdminStatsSerializer})
@api_view(["GET"])
@permission_classes([IsAdminUser])
@throttle_classes([_AdminThrottle])
def admin_stats(request):
    User = get_user_model()
    return Response({
        "users": User.objects.count(),
        "boards": Board.objects.count(),
        "tasks": Task.objects.count(),
        "contacts": Contact.objects.count(),
    })


urlpatterns = [
    path("health/", health),
    path("admin-api/stats/", admin_stats),
    path("auth/", include("auth_api.urls")),
    path("users/", include("users_api.urls")),
    path("boards/", include("boards_api.urls")),
    path("columns/", include("columns_api.urls")),
    path("tasks/", include("tasks_api.urls")),
    path("contacts/", include("contacts_api.urls")),
    path("notifications/", include("notifications_api.urls")),
    path("activity/", include("activity_api.urls")),
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
