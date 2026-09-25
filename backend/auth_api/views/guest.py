import uuid

from django.conf import settings
from django.contrib.auth.models import update_last_login
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from ..serializers import LoginResponseSerializer
from ._demo_data import create_demo_data
from ._helpers import User, issue_tokens_for, set_refresh_cookie


class GuestLoginThrottle(AnonRateThrottle):
    scope = "guest_login"


@extend_schema(request=None, responses={200: LoginResponseSerializer})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([GuestLoginThrottle])
def guest_login(request):
    with transaction.atomic():
        user = User.objects.create_user(
            email=f"guest-{uuid.uuid4().hex}@{settings.GUEST_EMAIL_DOMAIN}",
            password=None,
            first_name="Guest",
            last_name="Visitor",
            is_verified=True,
            is_guest=True,
        )
        create_demo_data(user)

    update_last_login(None, user)
    refresh, access = issue_tokens_for(user)
    response = Response({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_guest": user.is_guest,
        "totp_enabled": user.totp_enabled,
        "avatar_url": None,
        "access": str(access),
    })
    set_refresh_cookie(response, refresh)
    return response
