from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from columns_api.models import Column
from .models import Board

User = get_user_model()


class BoardListTests(APITestCase):
    url = "/boards/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_own_boards(self):
        Board.objects.create(title="My Board", created_by=self.user)
        Board.objects.create(title="Other Board", created_by=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "My Board")

    def test_create_board(self):
        response = self.client.post(self.url, {"title": "New Board"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Board")
        self.assertEqual(Board.objects.count(), 1)

    def test_create_board_creates_default_columns(self):
        self.client.post(self.url, {"title": "New Board"}, format="json")
        board = Board.objects.first()
        columns = list(Column.objects.filter(board=board).order_by("order").values_list("title", flat=True))
        self.assertEqual(columns, settings.DEFAULT_BOARD_COLUMNS)

    def test_create_board_missing_title(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="My Board", created_by=self.user)
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/boards/{pk}/"

    def test_get_board(self):
        response = self.client.get(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "My Board")

    def test_get_board_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_board(self):
        response = self.client.patch(self.url(self.board.pk), {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")

    def test_patch_other_board_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.url(self.board.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_board(self):
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 0)

    def test_delete_other_board_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_board_invalid_color(self):
        response = self.client.patch(self.url(self.board.pk), {"color": "not-a-color"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_board_valid_color(self):
        response = self.client.patch(self.url(self.board.pk), {"color": "#ff5733"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["color"], "#ff5733")
