from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from columns_api.models import Column
from contacts_api.models import Contact
from ..models import Task, Label, TaskDependency

User = get_user_model()


class TaskListTests(APITestCase):
    url = "/tasks/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        Column.objects.create(board=self.board, title="Default", order=0)
        self.client.force_authenticate(user=self.user)

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

    def test_create_task_invalid_priority(self):
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task", "priority": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/tasks/{pk}/"

    def test_get_task(self):
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Task")

    def test_get_task_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_task_query_count_independent_of_dependencies(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def query_count():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(self.url(self.task.pk))
            return len(ctx.captured_queries)

        TaskDependency.objects.create(task=self.task, depends_on=Task.objects.create(board=self.board, title="Dep 0"))
        baseline = query_count()
        for i in range(1, 4):
            TaskDependency.objects.create(task=self.task, depends_on=Task.objects.create(board=self.board, title=f"Dep {i}"))
        self.assertEqual(query_count(), baseline)

    def test_patch_task(self):
        response = self.client.patch(self.url(self.task.pk), {"title": "Updated", "priority": "high"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")
        self.assertEqual(response.data["priority"], "high")

    def test_patch_task_returns_404_for_other_user(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.url(self.task.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_task(self):
        response = self.client.delete(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.archived_at)

    def test_delete_task_returns_404_for_other_user(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_task_invalid_priority(self):
        response = self.client.patch(self.url(self.task.pk), {"priority": "invalid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_task_negative_order(self):
        response = self.client.patch(self.url(self.task.pk), {"order": -1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminAccessTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", is_superuser=True)
        self.board = Board.objects.create(title="Board", created_by=self.owner)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_list_tasks(self):
        response = self.client.get("/tasks/", {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_patch_task(self):
        response = self.client.patch(f"/tasks/{self.task.pk}/", {"title": "Admin Edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Admin Edit")

    def test_admin_can_delete_task(self):
        response = self.client.delete(f"/tasks/{self.task.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


@override_settings(DUE_DATE_REMINDER_HOURS=24)


class RecurringTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col1 = Column.objects.create(board=self.board, title="To do", order=0)
        self.col2 = Column.objects.create(board=self.board, title="Done", order=1)
        self.client.force_authenticate(user=self.user)

    def test_archive_recurring_creates_next(self):
        task = Task.objects.create(
            board=self.board, column=self.col2, title="Weekly Standup",
            due_date=timezone.now().date(), recurrence="weekly",
        )
        response = self.client.delete(f"/tasks/{task.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        new_task = Task.objects.filter(title="Weekly Standup", archived_at__isnull=True).first()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.due_date, task.due_date + timedelta(weeks=1))
        self.assertEqual(new_task.column, self.col1)
        self.assertEqual(new_task.recurrence, "weekly")

    def test_archive_non_recurring_no_new_task(self):
        task = Task.objects.create(
            board=self.board, column=self.col2, title="One-off",
            due_date=timezone.now().date(),
        )
        self.client.delete(f"/tasks/{task.pk}/")
        self.assertEqual(Task.objects.filter(archived_at__isnull=True).count(), 0)

    def test_archive_recurring_without_due_date_no_new_task(self):
        task = Task.objects.create(
            board=self.board, column=self.col2, title="No date",
            recurrence="daily",
        )
        self.client.delete(f"/tasks/{task.pk}/")
        self.assertEqual(Task.objects.filter(archived_at__isnull=True).count(), 0)

    def test_create_task_with_recurrence(self):
        response = self.client.post(
            f"/tasks/?board={self.board.pk}",
            {"title": "Daily", "due_date": "2026-05-01", "recurrence": "daily"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["recurrence"], "daily")

    def test_patch_recurrence(self):
        task = Task.objects.create(board=self.board, title="Task")
        response = self.client.patch(f"/tasks/{task.pk}/", {"recurrence": "monthly"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["recurrence"], "monthly")

    def test_patch_recurrence_null(self):
        task = Task.objects.create(board=self.board, title="Task", recurrence="weekly")
        response = self.client.patch(f"/tasks/{task.pk}/", {"recurrence": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["recurrence"])


class TaskListPermissionTests(APITestCase):
    url = "/tasks/"

    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.owner)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)

    def test_list_tasks_board_not_found(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url, {"board": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_tasks_outsider_gets_404(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url, {"board": self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_task_with_invalid_column(self):
        self.client.force_authenticate(user=self.owner)
        other_board = Board.objects.create(title="Other", created_by=self.owner)
        other_col = Column.objects.create(board=other_board, title="Other Col", order=0)
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task", "column": other_col.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid column", response.data["detail"])

    def test_create_task_with_valid_column(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task", "column": self.col.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["column"], self.col.pk)

    def test_create_task_with_invalid_assignee(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task", "assigned_to": [9999]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid contact", response.data["detail"])

    def test_create_task_with_valid_assignee(self):
        self.client.force_authenticate(user=self.owner)
        contact = Contact.objects.create(owner=self.owner, first_name="A", last_name="B", email="ab@example.com")
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task", "assigned_to": [contact.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(contact.pk, response.data["assigned_to"])

    def test_create_task_viewer_cannot_create(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role="viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.post(
            f"{self.url}?board={self.board.pk}",
            {"title": "Task"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TaskPatchAdvancedTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col1 = Column.objects.create(board=self.board, title="Todo", order=0)
        self.col2 = Column.objects.create(board=self.board, title="Done", order=1)
        self.task = Task.objects.create(board=self.board, column=self.col1, title="Task")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/tasks/{pk}/"

    def test_patch_task_with_invalid_assignee(self):
        response = self.client.patch(self.url(self.task.pk), {"assigned_to": [9999]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid contact", response.data["detail"])

    def test_patch_task_with_valid_assignee(self):
        contact = Contact.objects.create(owner=self.user, first_name="X", last_name="Y", email="xy@example.com")
        response = self.client.patch(self.url(self.task.pk), {"assigned_to": [contact.pk]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(contact.pk, response.data["assigned_to"])

    def test_patch_task_with_invalid_column(self):
        other_board = Board.objects.create(title="Other", created_by=self.user)
        other_col = Column.objects.create(board=other_board, title="Other Col", order=0)
        response = self.client.patch(self.url(self.task.pk), {"column": other_col.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid column", response.data["detail"])

    def test_patch_task_move_column(self):
        response = self.client.patch(self.url(self.task.pk), {"column": self.col2.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["column"], self.col2.pk)

    def test_patch_task_set_labels(self):
        label1 = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        label2 = Label.objects.create(board=self.board, name="Feature", color="#00ff00")
        response = self.client.patch(
            self.url(self.task.pk), {"label_ids": [label1.pk, label2.pk]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        label_names = {lb["name"] for lb in response.data["labels"]}
        self.assertEqual(label_names, {"Bug", "Feature"})

    def test_patch_task_clear_labels(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        self.task.labels.add(label)
        response = self.client.patch(self.url(self.task.pk), {"label_ids": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["labels"], [])

    def test_patch_task_viewer_cannot_edit(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role="viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.patch(self.url(self.task.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
