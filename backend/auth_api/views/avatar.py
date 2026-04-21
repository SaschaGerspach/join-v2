from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from ..serializers import AvatarSerializer

MAX_SIZE = 2 * 1024 * 1024


@extend_schema(request=AvatarSerializer, responses={200: AvatarSerializer})
@api_view(["POST", "DELETE"])
@parser_classes([MultiPartParser])
def avatar_upload(request):
    user = request.user

    if request.method == "DELETE":
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = ""
            user.save(update_fields=["avatar"])
        return Response({"avatar_url": None})

    file = request.FILES.get("avatar")
    if not file:
        return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    if file.size > MAX_SIZE:
        return Response({"detail": "File too large (max 2 MB)."}, status=status.HTTP_400_BAD_REQUEST)

    if not file.content_type.startswith("image/"):
        return Response({"detail": "Only image files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

    if user.avatar:
        user.avatar.delete(save=False)

    user.avatar = file
    user.save(update_fields=["avatar"])

    return Response({"avatar_url": request.build_absolute_uri(user.avatar.url)})
