from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from .models import ActivityEntry

User = get_user_model()


class ActivityListTests(APITestCase):
    url = "/activity/"

    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.member = User.objects.create_user(email="member@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.owner)
        BoardMember.objects.create(board=self.board, user=self.member)
        self.client.force_authenticate(user=self.owner)

    def test_list_activity(self):
        ActivityEntry.objects.create(board=self.board, user=self.owner, action="created", entity_type="task", entity_title="My Task")
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["entity_title"], "My Task")
        self.assertEqual(results[0]["action"], "created")

    def test_list_empty(self):
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
        self.assertFalse(response.data["has_more"])

    def test_list_as_member(self):
        ActivityEntry.objects.create(board=self.board, user=self.owner, action="created", entity_type="task", entity_title="Task")
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_forbidden_for_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_missing_board_param(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_board_not_found(self):
        response = self.client.get(self.url, {"board": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_ordered_newest_first(self):
        e1 = ActivityEntry.objects.create(board=self.board, user=self.owner, action="created", entity_type="task", entity_title="First")
        e2 = ActivityEntry.objects.create(board=self.board, user=self.owner, action="updated", entity_type="task", entity_title="Second")
        response = self.client.get(self.url, {"board": self.board.pk})
        results = response.data["results"]
        self.assertEqual(results[0]["id"], e2.pk)
        self.assertEqual(results[1]["id"], e1.pk)

    def test_list_max_50(self):
        for i in range(55):
            ActivityEntry.objects.create(board=self.board, user=self.owner, action="created", entity_type="task", entity_title=f"T{i}")
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(len(response.data["results"]), 50)
        self.assertTrue(response.data["has_more"])

    def test_user_name_in_response(self):
        self.owner.first_name = "Max"
        self.owner.last_name = "Mustermann"
        self.owner.save()
        ActivityEntry.objects.create(board=self.board, user=self.owner, action="created", entity_type="task", entity_title="T")
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.data["results"][0]["user_name"], "Max Mustermann")

    def test_deleted_user_name(self):
        temp = User.objects.create_user(email="temp@example.com", password="pass")
        ActivityEntry.objects.create(board=self.board, user=temp, action="created", entity_type="task", entity_title="T")
        temp.delete()
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.data["results"][0]["user_name"], "Deleted user")


class ActivityModelTests(APITestCase):
    def test_cascade_delete_board(self):
        user = User.objects.create_user(email="a@example.com", password="pass")
        board = Board.objects.create(title="B", created_by=user)
        ActivityEntry.objects.create(board=board, user=user, action="created", entity_type="task", entity_title="T")
        self.assertEqual(ActivityEntry.objects.count(), 1)
        board.delete()
        self.assertEqual(ActivityEntry.objects.count(), 0)

    def test_user_set_null_on_delete(self):
        user = User.objects.create_user(email="a@example.com", password="pass")
        board = Board.objects.create(title="B", created_by=user)
        temp = User.objects.create_user(email="temp@example.com", password="pass")
        entry = ActivityEntry.objects.create(board=board, user=temp, action="created", entity_type="task", entity_title="T")
        temp.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.user)
