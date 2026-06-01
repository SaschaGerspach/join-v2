import json

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from . import prompts
from .features import FEATURES, AIFeature
from .models import AIFeatureFlag
from .prompts import PRIORITIES
from .providers import provider_available
from .providers.base import AIDisabledError, AINotConfiguredError, AIProviderError
from .serializers import (
    AIFeatureListSerializer,
    AIFeatureUpdateSerializer,
    EnabledFeaturesSerializer,
    CategorizeInput,
    CategorizeOutput,
    DescriptionOutput,
    GenerateDescriptionInput,
    SubtasksOutput,
    SuggestSubtasksInput,
    SummarizeInput,
    SummaryOutput,
)
from .service import run_feature


class AIThrottle(UserRateThrottle):
    scope = "ai"


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


@extend_schema(responses=EnabledFeaturesSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enabled_features(request):
    keys = AIFeatureFlag.objects.filter(enabled=True).values_list("key", flat=True)
    return Response({"features": [key for key in keys if key in FEATURES]})


def _run(key, system, prompt, *, max_tokens=1024):
    """Invoke a feature and map AI errors to HTTP responses. Returns the raw
    model text on success, or a Response on failure (caller short-circuits)."""
    try:
        return run_feature(key, system, prompt, max_tokens=max_tokens), None
    except AIDisabledError:
        return None, Response(
            {"detail": "This AI feature is disabled."},
            status=status.HTTP_403_FORBIDDEN,
        )
    except AINotConfiguredError:
        return None, Response(
            {"detail": "AI is not configured on the server."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except AIProviderError:
        return None, Response(
            {"detail": "The AI provider request failed."},
            status=status.HTTP_502_BAD_GATEWAY,
        )


def _parse_json(raw):
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise AIProviderError("model did not return JSON")
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AIProviderError(str(exc)) from exc


def _validate(serializer_cls, data):
    serializer = serializer_cls(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _string_list(value):
    """Coerce a model-provided value into a clean list of non-empty strings.
    Guards against the model returning a string (which would iterate per char)
    or a non-list type instead of an array."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


@extend_schema(request=GenerateDescriptionInput, responses=DescriptionOutput)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIThrottle])
def generate_description(request):
    data = _validate(GenerateDescriptionInput, request.data)
    system, prompt = prompts.generate_description(data["title"], data.get("keywords", ""))
    raw, error = _run(AIFeature.GENERATE_DESCRIPTION, system, prompt, max_tokens=400)
    if error:
        return error
    return Response({"description": raw.strip()})


@extend_schema(request=SuggestSubtasksInput, responses=SubtasksOutput)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIThrottle])
def suggest_subtasks(request):
    data = _validate(SuggestSubtasksInput, request.data)
    system, prompt = prompts.suggest_subtasks(data["title"], data.get("description", ""))
    raw, error = _run(AIFeature.SUGGEST_SUBTASKS, system, prompt, max_tokens=400)
    if error:
        return error
    try:
        parsed = _parse_json(raw)
    except AIProviderError:
        return Response(
            {"detail": "The AI provider returned an unexpected response."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response({"subtasks": _string_list(parsed.get("subtasks"))})


@extend_schema(request=SummarizeInput, responses=SummaryOutput)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIThrottle])
def summarize(request):
    data = _validate(SummarizeInput, request.data)
    system, prompt = prompts.summarize(data["items"])
    raw, error = _run(AIFeature.SUMMARIZE, system, prompt, max_tokens=500)
    if error:
        return error
    return Response({"summary": raw.strip()})


@extend_schema(request=CategorizeInput, responses=CategorizeOutput)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIThrottle])
def categorize(request):
    data = _validate(CategorizeInput, request.data)
    system, prompt = prompts.categorize(data["title"], data.get("description", ""))
    raw, error = _run(AIFeature.CATEGORIZE, system, prompt, max_tokens=200)
    if error:
        return error
    try:
        parsed = _parse_json(raw)
    except AIProviderError:
        return Response(
            {"detail": "The AI provider returned an unexpected response."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    priority = parsed.get("priority", "medium")
    if priority not in PRIORITIES:
        priority = "medium"
    return Response({"priority": priority, "labels": _string_list(parsed.get("labels"))})
