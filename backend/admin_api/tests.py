from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from audit_api.models import AuditLog
from boards_api.models import Board
from tasks_api.models import Task

User = get_user_model()


class AdminApiTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@test.com", password="pass", is_staff=True)
        self.user = User.objects.create_user(email="user@test.com", password="pass")
        self.admin_token = str(AccessToken.for_user(self.admin))
        self.user_token = str(AccessToken.for_user(self.user))

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class AdminStatsTests(AdminApiTestCase):
    url = "/admin-api/stats/"

    def test_admin_can_access_stats(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("users", response.data)
        self.assertIn("boards", response.data)
        self.assertIn("tasks", response.data)

    def test_non_admin_forbidden(self):
        self.auth(self.user_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_forbidden(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_trend_structure(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        for key in ("users", "boards", "tasks"):
            trend = response.data[key]
            self.assertIn("total", trend)
            self.assertIn("this_week", trend)
            self.assertIn("last_week", trend)


class AdminAuditLogTests(AdminApiTestCase):
    url = "/admin-api/audit-log/"

    def test_admin_can_access_audit_log(self):
        AuditLog.objects.create(user=self.admin, event_type="login_success", detail="test")
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("event_types", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_event_type(self):
        AuditLog.objects.create(user=self.admin, event_type="login_success")
        AuditLog.objects.create(user=self.admin, event_type="login_failed")
        self.auth(self.admin_token)
        response = self.client.get(self.url, {"event_type": "login_success"})
        self.assertEqual(len(response.data["results"]), 1)

    def test_limit_parameter(self):
        for _ in range(5):
            AuditLog.objects.create(user=self.admin, event_type="login_success")
        self.auth(self.admin_token)
        response = self.client.get(self.url, {"limit": 2})
        self.assertEqual(len(response.data["results"]), 2)

    def test_limit_capped_at_100(self):
        self.auth(self.admin_token)
        response = self.client.get(self.url, {"limit": 999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_forbidden(self):
        self.auth(self.user_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBoardsTests(AdminApiTestCase):
    url = "/admin-api/boards/"

    def test_admin_can_access_boards(self):
        Board.objects.create(title="B1", created_by=self.user)
        self.auth(self.admin_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("active_boards", response.data)
        self.assertIn("inactive_boards", response.data)
        self.assertIn("top_boards", response.data)
        self.assertIn("recent_boards", response.data)

    def test_non_admin_forbidden(self):
        self.auth(self.user_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
