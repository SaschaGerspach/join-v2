
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from ..models import Task, TaskDependency

User = get_user_model()


class TaskArchiveTests(APITestCase):
    archive_url = "/tasks/archive/"

    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.member = User.objects.create_user(email="member@example.com", password="pass")
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", is_superuser=True)
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.owner)
        BoardMember.objects.create(board=self.board, user=self.member)
        self.task = Task.objects.create(board=self.board, title="Archived Task", archived_at=timezone.now())
        self.active_task = Task.objects.create(board=self.board, title="Active Task")
        self.client.force_authenticate(user=self.owner)

    def restore_url(self, pk):
        return f"/tasks/{pk}/restore/"

    def test_list_archive_as_owner(self):
        response = self.client.get(self.archive_url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Archived Task")

    def test_list_archive_query_count_independent_of_task_count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def query_count():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(self.archive_url, {"board": self.board.pk})
            return len(ctx.captured_queries)

        TaskDependency.objects.create(task=self.task, depends_on=self.active_task)
        baseline = query_count()
        for i in range(3):
            archived = Task.objects.create(board=self.board, title=f"Archived {i}", archived_at=timezone.now())
            TaskDependency.objects.create(task=archived, depends_on=self.active_task)
        self.assertEqual(query_count(), baseline)

    def test_list_archive_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.archive_url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_archive_as_board_admin(self):
        board_admin = User.objects.create_user(email="badmin@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=board_admin, role=BoardMember.Role.ADMIN)
        self.client.force_authenticate(user=board_admin)
        response = self.client.get(self.archive_url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_archive_forbidden_for_member(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.archive_url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_archive_forbidden_for_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.archive_url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_archive_missing_board(self):
        response = self.client.get(self.archive_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_task_as_owner(self):
        response = self.client.post(self.restore_url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.archived_at)

    def test_restore_task_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.restore_url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.archived_at)

    def test_restore_forbidden_for_member(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self.restore_url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restore_not_found_for_active_task(self):
        response = self.client.post(self.restore_url(self.active_task.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_restore_not_found_nonexistent(self):
        response = self.client.post(self.restore_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_soft_delete_hides_from_list(self):
        response = self.client.get("/tasks/", {"board": self.board.pk})
        titles = [t["title"] for t in response.data]
        self.assertNotIn("Archived Task", titles)
        self.assertIn("Active Task", titles)

    def test_soft_delete_hides_from_detail(self):
        response = self.client.get(f"/tasks/{self.task.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
