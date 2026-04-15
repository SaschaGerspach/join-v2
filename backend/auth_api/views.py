from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from config.serializers import DetailSerializer

from .serializers import (
    AccessTokenSerializer,
    EmailSerializer,
    LoginErrorSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
)


def _set_refresh_cookie(response, token):
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


def _clear_refresh_cookie(response):
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None),
    )


def _issue_tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return refresh, refresh.access_token


class AuthRateThrottle(AnonRateThrottle):
    rate = "10/minute"
    scope = "auth_attempts"


User = get_user_model()


@extend_schema(
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    first_name = request.data.get("first_name", "").strip()
    last_name = request.data.get("last_name", "").strip()

    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return Response(
            {"detail": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"detail": "A user with this email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    _send_verification_email(user)

    return Response(
        {"id": user.pk, "email": user.email},
        status=status.HTTP_201_CREATED,
    )


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
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")

    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

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

    refresh, access = _issue_tokens_for(user)
    response = Response({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "access": str(access),
    })
    _set_refresh_cookie(response, refresh)
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
    _clear_refresh_cookie(response)
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
        _clear_refresh_cookie(response)
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
    _set_refresh_cookie(response, refresh)
    return response


def _send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"
    send_mail(
        subject="Verify your email — Join",
        message=f"Welcome to Join! Please verify your email:\n\n{verify_url}\n\nThis link expires in 1 hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@extend_schema(
    request=VerifyEmailSerializer,
    responses={204: None, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    uid = request.data.get("uid", "")
    token = request.data.get("token", "")

    if not uid or not token:
        return Response({"detail": "uid and token are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"detail": "Link expired or already used."}, status=status.HTTP_400_BAD_REQUEST)

    user.is_verified = True
    user.save(update_fields=["is_verified"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=EmailSerializer,
    responses={204: None, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def resend_verification(request):
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)

    if not user.is_verified:
        _send_verification_email(user)

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=EmailSerializer,
    responses={204: None, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def password_reset_request(request):
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    send_mail(
        subject="Password Reset — Join",
        message=f"Click the link to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={204: None, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    uid = request.data.get("uid", "")
    token = request.data.get("token", "")
    password = request.data.get("password", "")

    if not uid or not token or not password:
        return Response({"detail": "uid, token and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"detail": "Link expired or already used."}, status=status.HTTP_400_BAD_REQUEST)

    form = SetPasswordForm(user, {"new_password1": password, "new_password2": password})
    if not form.is_valid():
        errors = [e for errors in form.errors.values() for e in errors]
        return Response({"detail": errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    form.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


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
