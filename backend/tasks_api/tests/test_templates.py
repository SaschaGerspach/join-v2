from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from columns_api.models import Column
from ..models import Task, TaskTemplate

User = get_user_model()


class TaskTemplateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        Column.objects.create(board=self.board, title="Todo", order=0)
        self.template = TaskTemplate.objects.create(board=self.board, name="Bug", title="Bug report", subtasks=["Reproduce"])
        self.client.force_authenticate(user=self.user)

    def detail_url(self, pk):
        return f"/tasks/templates/{pk}/"

    def create_task_url(self, pk):
        return f"/tasks/templates/{pk}/create-task/"

    def test_patch_template(self):
        response = self.client.patch(self.detail_url(self.template.pk), {"name": "Defect"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Defect")

    def test_create_task_from_template(self):
        response = self.client.post(self.create_task_url(self.template.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Bug report")
        self.assertEqual(Task.objects.get(pk=response.data["id"]).subtasks.count(), 1)

    def test_outsider_gets_404(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.delete(self.detail_url(self.template.pk)).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(self.create_task_url(self.template.pk)).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(TaskTemplate.objects.filter(pk=self.template.pk).exists())

    def test_viewer_forbidden(self):
        BoardMember.objects.create(board=self.board, user=self.other, role="viewer")
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.delete(self.detail_url(self.template.pk)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(self.create_task_url(self.template.pk)).status_code, status.HTTP_403_FORBIDDEN)
