from abc import ABC, abstractmethod


class AIError(Exception):
    """Base class for all AI feature errors."""


class AIDisabledError(AIError):
    """The requested feature is toggled off."""


class AINotConfiguredError(AIError):
    """The feature is on but no usable provider/credentials are configured."""


class AIProviderError(AIError):
    """The upstream provider call failed."""


class AIProvider(ABC):
    default_model = ""

    def __init__(self, api_key, model=""):
        self._api_key = api_key
        self._model = model or self.default_model

    @abstractmethod
    def generate(self, system: str, prompt: str, *, max_tokens: int = 1024) -> str:
        """Return the model's text response for the given system + user prompt."""
