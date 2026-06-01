from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .features import FEATURES
from .models import AIFeatureFlag
from .providers import provider_available
from .serializers import AIFeatureListSerializer, AIFeatureUpdateSerializer


def _feature_list():
    enabled_keys = set(
        AIFeatureFlag.objects.filter(enabled=True).values_list("key", flat=True)
    )
    return {
        "provider": settings.AI_PROVIDER,
        "configured": provider_available(),
        "features": [
            {
                "key": key,
                "label": meta["label"],
                "description": meta["description"],
                "enabled": key in enabled_keys,
            }
            for key, meta in FEATURES.items()
        ],
    }


@extend_schema(responses=AIFeatureListSerializer)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_features(request):
    return Response(_feature_list())


@extend_schema(request=AIFeatureUpdateSerializer, responses=AIFeatureListSerializer)
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def admin_feature_detail(request, key):
    if key not in FEATURES:
        return Response(
            {"detail": "Unknown feature."}, status=status.HTTP_404_NOT_FOUND
        )
    serializer = AIFeatureUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    AIFeatureFlag.objects.update_or_create(
        key=key,
        defaults={
            "enabled": serializer.validated_data["enabled"],
            "updated_by": request.user,
        },
    )
    return Response(_feature_list())
