from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

from .features import AIFeature
from .models import AIFeatureFlag
from .providers import get_provider, provider_available
from .providers.anthropic_provider import AnthropicProvider
from .providers.base import AIDisabledError, AINotConfiguredError, AIProviderError
from .providers.openai_provider import OpenAIProvider
from .service import run_feature

User = get_user_model()


class AIBaseTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com", password="pass", is_staff=True
        )
        self.user = User.objects.create_user(email="user@test.com", password="pass")
        self.admin_token = str(AccessToken.for_user(self.admin))
        self.user_token = str(AccessToken.for_user(self.user))

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class AdminFeatureListTests(AIBaseTestCase):
    url = "/ai/admin/features/"

    def test_admin_lists_all_features_disabled_by_default(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["features"]), 4)
        self.assertTrue(all(not f["enabled"] for f in response.data["features"]))

    def test_non_admin_forbidden(self):
        self.auth(self.user_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_forbidden(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(AI_API_KEY="", AI_PROVIDER="anthropic")
    def test_configured_false_without_key(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertFalse(response.data["configured"])

    @override_settings(AI_API_KEY="sk-test", AI_PROVIDER="anthropic")
    def test_configured_true_with_key(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertTrue(response.data["configured"])


class AdminFeatureToggleTests(AIBaseTestCase):
    def url(self, key):
        return f"/ai/admin/features/{key}/"

    def test_admin_enables_feature(self):
        self.auth(self.admin_token)
        response = self.client.patch(
            self.url(AIFeature.SUGGEST_SUBTASKS), {"enabled": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flag = AIFeatureFlag.objects.get(key=AIFeature.SUGGEST_SUBTASKS)
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.updated_by, self.admin)

    def test_admin_disables_feature(self):
        AIFeatureFlag.objects.create(key=AIFeature.SUMMARIZE, enabled=True)
        self.auth(self.admin_token)
        response = self.client.patch(
            self.url(AIFeature.SUMMARIZE), {"enabled": False}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AIFeatureFlag.objects.get(key=AIFeature.SUMMARIZE).enabled)

    def test_unknown_feature_404(self):
        self.auth(self.admin_token)
        response = self.client.patch(self.url("nonsense"), {"enabled": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_toggle(self):
        self.auth(self.user_token)
        response = self.client.patch(
            self.url(AIFeature.CATEGORIZE), {"enabled": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ServiceGuardTests(AIBaseTestCase):
    def test_run_feature_disabled_raises_before_provider(self):
        # No flag enabled and no key set: must fail as disabled, not as misconfigured.
        with self.assertRaises(AIDisabledError):
            run_feature(AIFeature.GENERATE_DESCRIPTION, "sys", "prompt")

    @override_settings(AI_API_KEY="", AI_PROVIDER="anthropic")
    def test_get_provider_without_key_raises(self):
        with self.assertRaises(AINotConfiguredError):
            get_provider()

    @override_settings(AI_API_KEY="sk-test", AI_PROVIDER="unknown")
    def test_get_provider_unknown_provider_raises(self):
        with self.assertRaises(AINotConfiguredError):
            get_provider()

    @override_settings(AI_API_KEY="sk-test", AI_PROVIDER="anthropic", AI_MODEL="m")
    def test_get_provider_returns_configured_provider(self):
        provider = get_provider()
        self.assertIsInstance(provider, AnthropicProvider)

    @override_settings(AI_API_KEY="", AI_PROVIDER="anthropic")
    def test_provider_available_false_without_key(self):
        self.assertFalse(provider_available())


class EnabledFeaturesTests(AIBaseTestCase):
    url = "/ai/features/"

    def test_lists_only_enabled_keys(self):
        AIFeatureFlag.objects.create(key=AIFeature.SUGGEST_SUBTASKS, enabled=True)
        AIFeatureFlag.objects.create(key=AIFeature.SUMMARIZE, enabled=False)
        self.auth(self.user_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["features"], [AIFeature.SUGGEST_SUBTASKS])

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FeatureEndpointTests(AIBaseTestCase):
    def enable(self, key):
        AIFeatureFlag.objects.create(key=key, enabled=True)

    def test_disabled_feature_returns_403_before_touching_credentials(self):
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/generate-description/", {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_401(self):
        response = self.client.post(
            "/ai/generate-description/", {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(AI_API_KEY="")
    def test_enabled_without_key_returns_503(self):
        self.enable(AIFeature.GENERATE_DESCRIPTION)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/generate-description/", {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_generate_description_success(self, mock_get):
        mock_get.return_value.generate.return_value = "  A nice description.  "
        self.enable(AIFeature.GENERATE_DESCRIPTION)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/generate-description/", {"title": "Build login"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "A nice description.")

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_suggest_subtasks_parses_fenced_json(self, mock_get):
        mock_get.return_value.generate.return_value = (
            '```json\n{"subtasks": ["A", "B"]}\n```'
        )
        self.enable(AIFeature.SUGGEST_SUBTASKS)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/suggest-subtasks/", {"title": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subtasks"], ["A", "B"])

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_suggest_subtasks_invalid_json_returns_502(self, mock_get):
        mock_get.return_value.generate.return_value = "not json at all"
        self.enable(AIFeature.SUGGEST_SUBTASKS)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/suggest-subtasks/", {"title": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_categorize_clamps_invalid_priority(self, mock_get):
        mock_get.return_value.generate.return_value = (
            '{"priority": "wat", "labels": ["bug"]}'
        )
        self.enable(AIFeature.CATEGORIZE)
        self.auth(self.user_token)
        response = self.client.post("/ai/categorize/", {"title": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["priority"], "medium")
        self.assertEqual(response.data["labels"], ["bug"])

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_summarize_success(self, mock_get):
        mock_get.return_value.generate.return_value = "Summary text."
        self.enable(AIFeature.SUMMARIZE)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/summarize/", {"items": ["Task A", "Task B"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"], "Summary text.")

    def test_summarize_requires_items(self):
        self.enable(AIFeature.SUMMARIZE)
        self.auth(self.user_token)
        response = self.client.post("/ai/summarize/", {"items": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_provider_failure_returns_502(self, mock_get):
        mock_get.return_value.generate.side_effect = AIProviderError("boom")
        self.enable(AIFeature.GENERATE_DESCRIPTION)
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/generate-description/", {"title": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_categorize_passes_valid_priority(self, mock_get):
        mock_get.return_value.generate.return_value = (
            '{"priority": "urgent", "labels": ["api", " ", "bug"]}'
        )
        self.enable(AIFeature.CATEGORIZE)
        self.auth(self.user_token)
        response = self.client.post("/ai/categorize/", {"title": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["priority"], "urgent")
        self.assertEqual(response.data["labels"], ["api", "bug"])

    @override_settings(AI_API_KEY="sk-test")
    @patch("ai_api.service.get_provider")
    def test_categorize_malformed_json_returns_502(self, mock_get):
        # Braces present but not valid JSON: exercises the JSONDecodeError branch.
        mock_get.return_value.generate.return_value = "{priority: urgent}"
        self.enable(AIFeature.CATEGORIZE)
        self.auth(self.user_token)
        response = self.client.post("/ai/categorize/", {"title": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_suggest_subtasks_disabled_returns_403(self):
        self.auth(self.user_token)
        response = self.client.post("/ai/suggest-subtasks/", {"title": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summarize_disabled_returns_403(self):
        self.auth(self.user_token)
        response = self.client.post(
            "/ai/summarize/", {"items": ["A"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_categorize_disabled_returns_403(self):
        self.auth(self.user_token)
        response = self.client.post("/ai/categorize/", {"title": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ModelTests(APITestCase):
    def test_str_reflects_state(self):
        flag = AIFeatureFlag.objects.create(key=AIFeature.SUMMARIZE, enabled=True)
        self.assertEqual(str(flag), f"{AIFeature.SUMMARIZE}: on")
        flag.enabled = False
        self.assertEqual(str(flag), f"{AIFeature.SUMMARIZE}: off")

    def test_is_enabled_unknown_key_is_false(self):
        AIFeatureFlag.objects.create(key="bogus", enabled=True)
        self.assertFalse(AIFeatureFlag.is_enabled("bogus"))


class AnthropicProviderTests(SimpleTestCase):
    def _fake_sdk(self):
        block = MagicMock(type="text", text="Hello")
        message = MagicMock(content=[block])
        client = MagicMock()
        client.messages.create.return_value = message
        sdk = MagicMock()
        sdk.Anthropic.return_value = client
        return sdk, client

    def test_generate_builds_client_and_extracts_text(self):
        sdk, client = self._fake_sdk()
        with patch.dict("sys.modules", {"anthropic": sdk}):
            result = AnthropicProvider(api_key="sk", model="m").generate(
                "system", "prompt", max_tokens=42
            )
        self.assertEqual(result, "Hello")
        sdk.Anthropic.assert_called_once_with(api_key="sk")
        kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "m")
        self.assertEqual(kwargs["system"], "system")
        self.assertEqual(kwargs["max_tokens"], 42)

    def test_default_model_used_when_unset(self):
        sdk, client = self._fake_sdk()
        with patch.dict("sys.modules", {"anthropic": sdk}):
            AnthropicProvider(api_key="sk").generate("s", "p")
        self.assertEqual(
            client.messages.create.call_args.kwargs["model"],
            AnthropicProvider.default_model,
        )

    def test_sdk_error_is_wrapped(self):
        sdk = MagicMock()
        sdk.Anthropic.side_effect = RuntimeError("boom")
        with patch.dict("sys.modules", {"anthropic": sdk}):
            with self.assertRaises(AIProviderError):
                AnthropicProvider(api_key="sk").generate("s", "p")

    def test_missing_sdk_is_wrapped(self):
        with patch.dict("sys.modules", {"anthropic": None}):
            with self.assertRaises(AIProviderError):
                AnthropicProvider(api_key="sk").generate("s", "p")


class OpenAIProviderTests(SimpleTestCase):
    def _fake_sdk(self):
        choice = MagicMock()
        choice.message.content = "Hi"
        response = MagicMock(choices=[choice])
        client = MagicMock()
        client.chat.completions.create.return_value = response
        sdk = MagicMock()
        sdk.OpenAI.return_value = client
        return sdk, client

    def test_generate_builds_client_and_extracts_text(self):
        sdk, client = self._fake_sdk()
        with patch.dict("sys.modules", {"openai": sdk}):
            result = OpenAIProvider(api_key="sk", model="m").generate(
                "system", "prompt", max_tokens=42
            )
        self.assertEqual(result, "Hi")
        sdk.OpenAI.assert_called_once_with(api_key="sk")
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["content"], "prompt")

    def test_none_content_becomes_empty_string(self):
        sdk, client = self._fake_sdk()
        client.chat.completions.create.return_value.choices[0].message.content = None
        with patch.dict("sys.modules", {"openai": sdk}):
            result = OpenAIProvider(api_key="sk").generate("s", "p")
        self.assertEqual(result, "")

    def test_sdk_error_is_wrapped(self):
        sdk = MagicMock()
        sdk.OpenAI.side_effect = RuntimeError("boom")
        with patch.dict("sys.modules", {"openai": sdk}):
            with self.assertRaises(AIProviderError):
                OpenAIProvider(api_key="sk").generate("s", "p")

    def test_missing_sdk_is_wrapped(self):
        with patch.dict("sys.modules", {"openai": None}):
            with self.assertRaises(AIProviderError):
                OpenAIProvider(api_key="sk").generate("s", "p")
