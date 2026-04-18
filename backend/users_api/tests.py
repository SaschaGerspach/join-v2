from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember

User = get_user_model()


class UserListTests(APITestCase):
    url = "/users/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        self.client.force_authenticate(user=self.user)

    def test_list_returns_all_active_users(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        self.other = User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        self.client.force_authenticate(user=self.user)

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

    def test_delete_transfers_board_to_member(self):
        board = Board.objects.create(title="Team", created_by=self.user)
        BoardMember.objects.create(board=board, user=self.other)
        self.client.delete(self.url(self.user.pk))
        board.refresh_from_db()
        self.assertEqual(board.created_by, self.other)
        self.assertFalse(BoardMember.objects.filter(board=board, user=self.other).exists())

    def test_delete_removes_board_without_members(self):
        board = Board.objects.create(title="Solo", created_by=self.user)
        board_id = board.pk
        self.client.delete(self.url(self.user.pk))
        self.assertFalse(Board.objects.filter(pk=board_id).exists())

    def test_delete_removes_memberships(self):
        board = Board.objects.create(title="Other", created_by=self.other)
        BoardMember.objects.create(board=board, user=self.user)
        self.client.delete(self.url(self.user.pk))
        self.assertFalse(BoardMember.objects.filter(user=self.user).exists())
