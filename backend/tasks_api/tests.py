from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from .models import Task, Subtask

User = get_user_model()


class TaskListTests(APITestCase):
    url = "/tasks/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.client.login(username="a@example.com", password="pass")

    def test_list_tasks(self):
        Task.objects.create(board=self.board, title="Task 1")
        Task.objects.create(board=self.board, title="Task 2")
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_missing_board_param(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task(self):
        response = self.client.post(f"{self.url}?board={self.board.pk}", {"title": "New Task"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Task")

    def test_create_task_missing_title(self):
        response = self.client.post(f"{self.url}?board={self.board.pk}", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.login(username="a@example.com", password="pass")

    def url(self, pk):
        return f"/tasks/{pk}/"

    def test_get_task(self):
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Task")

    def test_get_task_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_task(self):
        response = self.client.patch(self.url(self.task.pk), {"title": "Updated", "priority": "high"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")
        self.assertEqual(response.data["priority"], "high")

    def test_patch_task_forbidden(self):
        self.client.logout()
        self.client.login(username="b@example.com", password="pass")
        response = self.client.patch(self.url(self.task.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_task(self):
        response = self.client.delete(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_task_forbidden(self):
        self.client.logout()
        self.client.login(username="b@example.com", password="pass")
        response = self.client.delete(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubtaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.login(username="a@example.com", password="pass")

    def list_url(self):
        return f"/tasks/{self.task.pk}/subtasks/"

    def detail_url(self, pk):
        return f"/tasks/{self.task.pk}/subtasks/{pk}/"

    def test_list_subtasks(self):
        Subtask.objects.create(task=self.task, title="Sub 1")
        Subtask.objects.create(task=self.task, title="Sub 2")
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_subtask(self):
        response = self.client.post(self.list_url(), {"title": "New Sub"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Sub")
        self.assertFalse(response.data["done"])

    def test_patch_subtask_done(self):
        subtask = Subtask.objects.create(task=self.task, title="Sub")
        response = self.client.patch(self.detail_url(subtask.pk), {"done": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["done"])

    def test_patch_subtask_forbidden(self):
        subtask = Subtask.objects.create(task=self.task, title="Sub")
        self.client.logout()
        self.client.login(username="b@example.com", password="pass")
        response = self.client.patch(self.detail_url(subtask.pk), {"done": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_subtask(self):
        subtask = Subtask.objects.create(task=self.task, title="Sub")
        response = self.client.delete(self.detail_url(subtask.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subtask.objects.count(), 0)
