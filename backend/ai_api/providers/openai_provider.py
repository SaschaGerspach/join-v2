from .base import AIProvider, AIProviderError


class OpenAIProvider(AIProvider):
    default_model = "gpt-4o-mini"

    def generate(self, system, prompt, *, max_tokens=1024):
        try:
            import openai
        except ImportError as exc:
            raise AIProviderError("openai SDK is not installed") from exc
        try:
            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        return response.choices[0].message.content or ""
