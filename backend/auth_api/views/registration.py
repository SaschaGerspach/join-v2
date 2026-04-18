from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.serializers import DetailSerializer
from ..serializers import RegisterResponseSerializer, RegisterSerializer
from ._helpers import AuthRateThrottle, User
from .verification import send_verification_email


@extend_schema(
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer, 400: DetailSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    email = data["email"].strip().lower()
    password = data["password"]
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    if User.objects.filter(email=email).exists():
        return Response(
            {"email": email},
            status=status.HTTP_201_CREATED,
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    send_verification_email(user)

    return Response(
        {"email": user.email},
        status=status.HTTP_201_CREATED,
    )
