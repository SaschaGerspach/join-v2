from django.conf import settings

from .base import AINotConfiguredError, AIProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


def get_provider() -> AIProvider:
    """Build the configured provider. Raises AINotConfiguredError when the
    credentials or provider selection are missing/unknown, so callers can map
    that to a clear 503 instead of crashing."""
    if not settings.AI_API_KEY:
        raise AINotConfiguredError("AI_API_KEY is not set")
    provider_cls = _PROVIDERS.get(settings.AI_PROVIDER)
    if provider_cls is None:
        raise AINotConfiguredError(f"Unknown AI provider: {settings.AI_PROVIDER!r}")
    return provider_cls(api_key=settings.AI_API_KEY, model=settings.AI_MODEL)


def provider_available() -> bool:
    return bool(settings.AI_API_KEY) and settings.AI_PROVIDER in _PROVIDERS
