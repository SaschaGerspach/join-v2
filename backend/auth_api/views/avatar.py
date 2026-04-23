import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from drf_spectacular.utils import extend_schema
from PIL import Image
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from ..serializers import AvatarSerializer

MAX_SIZE = 2 * 1024 * 1024
AVATAR_MAX_PX = 256


def _resize_avatar(file):
    img = Image.open(file)
    img = img.convert("RGB")
    if img.width > AVATAR_MAX_PX or img.height > AVATAR_MAX_PX:
        img.thumbnail((AVATAR_MAX_PX, AVATAR_MAX_PX), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return InMemoryUploadedFile(buf, "avatar", file.name.rsplit(".", 1)[0] + ".jpg", "image/jpeg", buf.getbuffer().nbytes, None)


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

    try:
        user.avatar = _resize_avatar(file)
    except Exception:
        return Response({"detail": "Invalid image file."}, status=status.HTTP_400_BAD_REQUEST)
    user.save(update_fields=["avatar"])

    return Response({"avatar_url": request.build_absolute_uri(user.avatar.url)})
