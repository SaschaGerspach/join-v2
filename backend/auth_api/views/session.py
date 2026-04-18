from django.conf import settings
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from config.serializers import DetailSerializer
from ..serializers import (
    AccessTokenSerializer,
    LoginErrorSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MeSerializer,
)
from ._helpers import AuthRateThrottle, clear_refresh_cookie, issue_tokens_for, set_refresh_cookie


@extend_schema(
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: DetailSerializer,
        401: DetailSerializer,
        403: LoginErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    email = data["email"].strip().lower()
    password = data["password"]

    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_verified:
        return Response(
            {"detail": "Please verify your email address before logging in.", "code": "email_not_verified"},
            status=status.HTTP_403_FORBIDDEN,
        )

    refresh, access = issue_tokens_for(user)
    response = Response({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "access": str(access),
    })
    set_refresh_cookie(response, refresh)
    return response


@extend_schema(request=None, responses={204: None})
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if raw:
        try:
            RefreshToken(raw).blacklist()
        except TokenError:
            pass
    response = Response(status=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response)
    return response


@extend_schema(
    request=None,
    responses={200: AccessTokenSerializer, 401: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request):
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if not raw:
        return Response({"detail": "No refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        refresh = RefreshToken(raw)
    except TokenError:
        response = Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        clear_refresh_cookie(response)
        return response

    access = refresh.access_token

    if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
        if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION"):
            try:
                refresh.blacklist()
            except AttributeError:
                pass
        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

    response = Response({"access": str(access)})
    set_refresh_cookie(response, refresh)
    return response


@extend_schema(responses={200: MeSerializer})
@api_view(["GET"])
def me(request):
    user = request.user
    return Response({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
    })
