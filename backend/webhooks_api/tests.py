from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from .models import Webhook, WebhookDelivery

User = get_user_model()

MOCK_RESOLVE = [(2, 1, 6, "", ("93.184.216.34", 443))]


class WebhookListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        BoardMember.objects.create(board=self.board, user=self.viewer, role="viewer")
        self.client.force_authenticate(user=self.user)

    def url(self):
        return f"/webhooks/?board={self.board.pk}"

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_create_webhook(self, _mock):
        response = self.client.post(self.url(), {
            "url": "https://example.com/hook",
            "events": ["task_created"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["url"], "https://example.com/hook")
        self.assertEqual(Webhook.objects.count(), 1)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_list_webhooks(self, _mock):
        Webhook.objects.create(board=self.board, url="https://example.com/hook1", events=["task_created"])
        Webhook.objects.create(board=self.board, url="https://example.com/hook2", events=["task_updated"])
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_missing_board_param(self):
        response = self.client.get("/webhooks/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_nonexistent_board(self):
        response = self.client.get("/webhooks/?board=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_outsider_gets_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_gets_403(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_create_invalid_events(self, _mock):
        response = self.client.post(self.url(), {
            "url": "https://example.com/hook",
            "events": ["nonexistent_event"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_url(self):
        response = self.client.post(self.url(), {
            "events": ["task_created"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_create_with_secret(self, _mock):
        response = self.client.post(self.url(), {
            "url": "https://example.com/hook",
            "events": ["task_created"],
            "secret": "my-secret",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        webhook = Webhook.objects.first()
        self.assertEqual(webhook.secret, "my-secret")

    def test_create_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url(), {
            "url": "https://example.com/hook",
            "events": ["task_created"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WebhookDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.webhook = Webhook.objects.create(
            board=self.board,
            url="https://example.com/hook",
            events=["task_created"],
        )
        self.client.force_authenticate(user=self.user)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_patch_webhook(self, _mock):
        response = self.client.patch(f"/webhooks/{self.webhook.pk}/", {
            "is_active": False,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.webhook.refresh_from_db()
        self.assertFalse(self.webhook.is_active)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_patch_webhook_url(self, _mock):
        response = self.client.patch(f"/webhooks/{self.webhook.pk}/", {
            "url": "https://example.com/new-hook",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.url, "https://example.com/new-hook")

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_patch_webhook_events(self, _mock):
        response = self.client.patch(f"/webhooks/{self.webhook.pk}/", {
            "events": ["task_updated", "task_deleted"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.events, ["task_updated", "task_deleted"])

    def test_delete_webhook(self):
        response = self.client.delete(f"/webhooks/{self.webhook.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Webhook.objects.count(), 0)

    def test_delete_nonexistent_webhook(self):
        response = self.client.delete("/webhooks/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_patch(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(f"/webhooks/{self.webhook.pk}/", {
            "is_active": False,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_delete(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/webhooks/{self.webhook.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("webhooks_api.serializers.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    def test_patch_invalid_events(self, _mock):
        response = self.client.patch(f"/webhooks/{self.webhook.pk}/", {
            "events": ["bogus"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WebhookDeliveriesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.webhook = Webhook.objects.create(
            board=self.board,
            url="https://example.com/hook",
            events=["task_created"],
        )
        self.client.force_authenticate(user=self.user)

    def test_list_deliveries(self):
        WebhookDelivery.objects.create(
            webhook=self.webhook, event_type="task_created",
            payload={"task": "test"}, status="success", response_status=200,
        )
        response = self.client.get(f"/webhooks/{self.webhook.pk}/deliveries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["event_type"], "task_created")

    def test_deliveries_nonexistent_webhook(self):
        response = self.client.get("/webhooks/99999/deliveries/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deliveries_outsider_gets_403(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f"/webhooks/{self.webhook.pk}/deliveries/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deliveries_empty(self):
        response = self.client.get(f"/webhooks/{self.webhook.pk}/deliveries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class WebhookEventsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_events(self):
        response = self.client.get("/webhooks/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("task_created", response.data)
        self.assertIn("task_updated", response.data)
        self.assertIn("task_deleted", response.data)


class WebhookDeliveryRetryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="B", created_by=self.user)
        self.webhook = Webhook.objects.create(
            board=self.board, url="https://example.com/hook", events=["task_created"],
        )

    @patch("webhooks_api.tasks.socket.getaddrinfo", return_value=MOCK_RESOLVE)
    @patch("webhooks_api.tasks.requests.post")
    def test_retry_reuses_same_delivery(self, mock_post, _mock_resolve):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "ok"
        from .tasks import deliver_webhook

        deliver_webhook.apply(args=(self.webhook.pk, "task_created", {"x": 1}))
        first = WebhookDelivery.objects.get(webhook=self.webhook)

        deliver_webhook.apply(
            args=(self.webhook.pk, "task_created", {"x": 1}),
            kwargs={"delivery_pk": first.pk},
        )

        self.assertEqual(WebhookDelivery.objects.filter(webhook=self.webhook).count(), 1)
        self.assertEqual(WebhookDelivery.objects.get(webhook=self.webhook).delivery_id, first.delivery_id)
