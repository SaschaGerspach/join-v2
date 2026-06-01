from .features import FEATURE_KEYS
from .models import AIFeatureFlag
from .providers import get_provider
from .providers.base import AIDisabledError


def run_feature(key, system, prompt, *, max_tokens=1024):
    """Guard + execute an AI feature.

    Order matters: we never touch credentials before confirming the feature is
    enabled, so a disabled feature can never trigger a provider call. Raises
    AIDisabledError (off), AINotConfiguredError (no key) or AIProviderError.
    """
    if key not in FEATURE_KEYS or not AIFeatureFlag.is_enabled(key):
        raise AIDisabledError(key)
    provider = get_provider()
    return provider.generate(system, prompt, max_tokens=max_tokens)
