from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from config.serializers import DetailSerializer


@extend_schema(responses={200: None})
@api_view(["GET"])
def session_list(request):
    tokens = (
        OutstandingToken.objects.filter(user=request.user, expires_at__gt=timezone.now())
        .exclude(id__in=BlacklistedToken.objects.values_list("token_id", flat=True))
        .order_by("-created_at")
    )
    current_jti = _get_current_jti(request)
    sessions = []
    for t in tokens:
        sessions.append({
            "id": t.pk,
            "created_at": t.created_at,
            "expires_at": t.expires_at,
            "is_current": t.jti == current_jti,
        })
    return Response(sessions)


@extend_schema(responses={204: None, 404: DetailSerializer})
@api_view(["DELETE"])
def session_revoke(request, pk):
    try:
        token = OutstandingToken.objects.get(pk=pk, user=request.user)
    except OutstandingToken.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        RefreshToken(token.token).blacklist()
    except Exception:
        pass
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={204: None})
@api_view(["POST"])
def session_revoke_all(request):
    current_jti = _get_current_jti(request)
    tokens = OutstandingToken.objects.filter(user=request.user, expires_at__gt=timezone.now()).exclude(
        id__in=BlacklistedToken.objects.values_list("token_id", flat=True)
    )
    for t in tokens:
        if t.jti == current_jti:
            continue
        try:
            RefreshToken(t.token).blacklist()
        except Exception:
            pass
    return Response(status=status.HTTP_204_NO_CONTENT)


def _get_current_jti(request):
    raw = request.COOKIES.get("refresh_token")
    if not raw:
        return None
    try:
        return RefreshToken(raw).payload.get("jti")
    except Exception:
        return None
