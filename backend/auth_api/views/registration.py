import hashlib
import time

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.serializers import DetailSerializer
from ..serializers import RegisterResponseSerializer, RegisterSerializer
from ._helpers import AuthRateThrottle, User
from ._demo_data import create_demo_data
from .verification import send_verification_email

_MIN_RESPONSE_TIME = 0.8
_PBKDF2_ITERATIONS = 100_000


def _constant_time_pad(email: str, start: float) -> None:
    hashlib.pbkdf2_hmac("sha256", email.encode(), b"register-pad", _PBKDF2_ITERATIONS)
    elapsed = time.monotonic() - start
    remaining = _MIN_RESPONSE_TIME - elapsed
    if remaining > 0:
        time.sleep(remaining)


@extend_schema(
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request):
    start = time.monotonic()

    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    email = data["email"].strip().lower()
    password = data["password"]
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        if settings.DEBUG:
            create_demo_data(user)
        send_verification_email(user)

    _constant_time_pad(email, start)

    return Response({"email": email}, status=status.HTTP_201_CREATED)
