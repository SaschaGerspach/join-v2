
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from columns_api.models import Column
from ..models import Task, TaskDependency

User = get_user_model()


class TaskDependencyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.task1 = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        self.task2 = Task.objects.create(board=self.board, column=self.col, title="Task 2")
        self.client.force_authenticate(user=self.user)

    def url(self, task_pk):
        return f"/tasks/{task_pk}/dependencies/"

    def detail_url(self, task_pk, pk):
        return f"/tasks/{task_pk}/dependencies/{pk}/"

    def test_add_dependency(self):
        response = self.client.post(self.url(self.task1.pk), {"depends_on": self.task2.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["depends_on"], self.task2.pk)
        self.assertEqual(response.data["title"], "Task 2")
        self.assertTrue(TaskDependency.objects.filter(task=self.task1, depends_on=self.task2).exists())

    def test_list_dependencies(self):
        TaskDependency.objects.create(task=self.task1, depends_on=self.task2)
        response = self.client.get(self.url(self.task1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["depends_on"], self.task2.pk)

    def test_delete_dependency(self):
        dep = TaskDependency.objects.create(task=self.task1, depends_on=self.task2)
        response = self.client.delete(self.detail_url(self.task1.pk, dep.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskDependency.objects.filter(pk=dep.pk).exists())

    def test_cannot_depend_on_self(self):
        response = self.client.post(self.url(self.task1.pk), {"depends_on": self.task1.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_circular_dependency_rejected(self):
        TaskDependency.objects.create(task=self.task1, depends_on=self.task2)
        response = self.client.post(self.url(self.task2.pk), {"depends_on": self.task1.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transitive_circular_dependency_rejected(self):
        task3 = Task.objects.create(board=self.board, column=self.col, title="Task 3")
        TaskDependency.objects.create(task=self.task1, depends_on=self.task2)
        TaskDependency.objects.create(task=self.task2, depends_on=task3)
        response = self.client.post(self.url(task3.pk), {"depends_on": self.task1.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_board_rejected(self):
        other_board = Board.objects.create(title="Other", created_by=self.user)
        other_task = Task.objects.create(board=other_board, title="Other Task")
        response = self.client.post(self.url(self.task1.pk), {"depends_on": other_task.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_idempotent_add(self):
        self.client.post(self.url(self.task1.pk), {"depends_on": self.task2.pk}, format="json")
        response = self.client.post(self.url(self.task1.pk), {"depends_on": self.task2.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskDependency.objects.filter(task=self.task1, depends_on=self.task2).count(), 1)

    def test_outsider_cannot_access(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url(self.task1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_serialization_includes_dependencies(self):
        TaskDependency.objects.create(task=self.task1, depends_on=self.task2)
        response = self.client.get(f"/tasks/{self.task1.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["dependencies"]), 1)
        self.assertEqual(response.data["dependencies"][0]["depends_on"], self.task2.pk)
