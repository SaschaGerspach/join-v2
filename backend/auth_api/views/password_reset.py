from django.conf import settings
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from config.mail import send_mail_async
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.serializers import DetailSerializer
from ..serializers import EmailSerializer, PasswordResetConfirmSerializer
from audit_api.helpers import log_audit
from ._helpers import AuthRateThrottle, User


@extend_schema(
    request=EmailSerializer,
    responses={204: None, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def password_reset_request(request):
    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data["email"].strip().lower()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    send_mail_async(
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
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]
    password = serializer.validated_data["password"]

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
    log_audit("password_reset", user=user, request=request)
    return Response(status=status.HTTP_204_NO_CONTENT)
