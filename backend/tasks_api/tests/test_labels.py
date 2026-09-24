
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from ..models import Label

User = get_user_model()


class LabelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.client.force_authenticate(user=self.user)

    def list_url(self):
        return f"/boards/{self.board.pk}/labels/"

    def detail_url(self, pk):
        return f"/boards/{self.board.pk}/labels/{pk}/"

    def test_create_label(self):
        response = self.client.post(self.list_url(), {"name": "Bug", "color": "#ff0000"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Bug")
        self.assertEqual(response.data["color"], "#ff0000")

    def test_create_label_invalid_color(self):
        response = self.client.post(self.list_url(), {"name": "Bug", "color": "red"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_label(self):
        Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        response = self.client.post(self.list_url(), {"name": "Bug", "color": "#00ff00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_labels(self):
        Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        Label.objects.create(board=self.board, name="Feature", color="#00ff00")
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_patch_label(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        response = self.client.patch(self.detail_url(label.pk), {"name": "Hotfix"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Hotfix")

    def test_delete_label(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        response = self.client.delete(self.detail_url(label.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Label.objects.count(), 0)

    def test_labels_forbidden_for_non_member(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
