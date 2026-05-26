from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from .models import Column

User = get_user_model()


class ColumnListTests(APITestCase):
    url = "/columns/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.client.force_authenticate(user=self.user)

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

    def test_create_column_editor_allowed(self):
        editor = User.objects.create_user(email="editor@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=editor, role=BoardMember.Role.EDITOR)
        self.client.force_authenticate(user=editor)
        response = self.client.post(f"{self.url}?board={self.board.pk}", {"title": "New"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_column_viewer_forbidden(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role=BoardMember.Role.VIEWER)
        self.client.force_authenticate(user=viewer)
        response = self.client.post(f"{self.url}?board={self.board.pk}", {"title": "New"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_columns_as_member(self):
        Column.objects.create(board=self.board, title="Todo", order=0)
        member = User.objects.create_user(email="member@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=member)
        self.client.force_authenticate(user=member)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ColumnDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.column = Column.objects.create(board=self.board, title="Todo", order=0)
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/columns/{pk}/"

    def test_patch_column(self):
        response = self.client.patch(self.url(self.column.pk), {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")

    def test_patch_column_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.url(self.column.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_column(self):
        response = self.client.delete(self.url(self.column.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Column.objects.count(), 0)

    def test_delete_column_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.url(self.column.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_column_editor_allowed(self):
        editor = User.objects.create_user(email="editor@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=editor, role=BoardMember.Role.EDITOR)
        self.client.force_authenticate(user=editor)
        response = self.client.delete(self.url(self.column.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_column_viewer_forbidden(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role=BoardMember.Role.VIEWER)
        self.client.force_authenticate(user=viewer)
        col = Column.objects.create(board=self.board, title="Extra", order=1)
        response = self.client.delete(self.url(col.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_column_editor_allowed(self):
        editor = User.objects.create_user(email="editor@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=editor, role=BoardMember.Role.EDITOR)
        self.client.force_authenticate(user=editor)
        response = self.client.patch(self.url(self.column.pk), {"title": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_column_viewer_forbidden(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role=BoardMember.Role.VIEWER)
        self.client.force_authenticate(user=viewer)
        response = self.client.patch(self.url(self.column.pk), {"title": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
