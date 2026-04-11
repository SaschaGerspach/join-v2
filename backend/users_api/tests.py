from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserListTests(APITestCase):
    url = "/users/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        self.client.login(username="a@example.com", password="pass")

    def test_list_returns_all_active_users(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        self.other = User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        self.client.login(username="a@example.com", password="pass")

    def url(self, pk):
        return f"/users/{pk}/"

    def test_get_user(self):
        response = self.client.get(self.url(self.user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "a@example.com")

    def test_get_user_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_profile(self):
        response = self.client.patch(self.url(self.user.pk), {"first_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_patch_other_profile_forbidden(self):
        response = self.client.patch(self.url(self.other.pk), {"first_name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_account(self):
        response = self.client.delete(self.url(self.user.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_delete_other_account_forbidden(self):
        response = self.client.delete(self.url(self.other.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
