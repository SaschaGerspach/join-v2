from django.conf import settings
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
from ..serializers import EmailSerializer, VerifyEmailSerializer
from ._helpers import AuthRateThrottle, User


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"
    send_mail_async(
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
    serializer = VerifyEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]

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
    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data["email"].strip().lower()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)

    if not user.is_verified:
        send_verification_email(user)

    return Response(status=status.HTTP_204_NO_CONTENT)
