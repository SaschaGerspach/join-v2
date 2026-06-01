from .base import AIProvider, AIProviderError


class AnthropicProvider(AIProvider):
    default_model = "claude-haiku-4-5-20251001"

    def generate(self, system, prompt, *, max_tokens=1024):
        try:
            import anthropic
        except ImportError as exc:
            raise AIProviderError("anthropic SDK is not installed") from exc
        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model=self._model,
                system=system,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        return "".join(block.text for block in message.content if block.type == "text")
