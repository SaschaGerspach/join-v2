from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from .models import Column

User = get_user_model()


class ColumnListTests(APITestCase):
    url = "/columns/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.client.login(username="a@example.com", password="pass")

    def test_list_columns(self):
        Column.objects.create(board=self.board, title="Todo", order=0)
        Column.objects.create(board=self.board, title="Done", order=1)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_missing_board_param(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_board_not_found(self):
        response = self.client.get(self.url, {"board": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_column(self):
        response = self.client.post(f"{self.url}?board={self.board.pk}", {"title": "In Progress"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "In Progress")

    def test_create_column_missing_title(self):
        response = self.client.post(f"{self.url}?board={self.board.pk}", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ColumnDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.column = Column.objects.create(board=self.board, title="Todo", order=0)
        self.client.login(username="a@example.com", password="pass")

    def url(self, pk):
        return f"/columns/{pk}/"

    def test_patch_column(self):
        response = self.client.patch(self.url(self.column.pk), {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")

    def test_patch_column_forbidden(self):
        self.client.logout()
        self.client.login(username="b@example.com", password="pass")
        response = self.client.patch(self.url(self.column.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_column(self):
        response = self.client.delete(self.url(self.column.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Column.objects.count(), 0)

    def test_delete_column_forbidden(self):
        self.client.logout()
        self.client.login(username="b@example.com", password="pass")
        response = self.client.delete(self.url(self.column.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
