from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.serializers import DetailSerializer
from .serializers import PublicUserSerializer, UserUpdateSerializer

User = get_user_model()


def serialize_user(user):
    return {
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@extend_schema(responses={200: PublicUserSerializer(many=True)})
@api_view(["GET"])
def user_list(request):
    users = User.objects.filter(is_active=True).order_by("id")
    return Response([serialize_user(u) for u in users])


@extend_schema(
    methods=["GET"],
    responses={200: PublicUserSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=UserUpdateSerializer,
    responses={200: PublicUserSerializer, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "PATCH", "DELETE"])
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serialize_user(user))

    if request.method == "PATCH":
        if request.user.pk != pk:
            return Response({"detail": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)
        for field in ["first_name", "last_name", "email"]:
            if field in request.data:
                setattr(user, field, request.data[field])
        if "password" in request.data:
            new_password = request.data["password"].strip()
            if len(new_password) < 8:
                return Response({"detail": "Password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
        user.save()
        return Response(serialize_user(user))

    if request.method == "DELETE":
        if request.user.pk != pk:
            return Response({"detail": "You can only delete your own account."}, status=status.HTTP_403_FORBIDDEN)
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
