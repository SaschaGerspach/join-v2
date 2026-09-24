from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from columns_api.models import Column
from contacts_api.models import Contact
from ..models import Task, Subtask, Label

User = get_user_model()


class TaskReorderTests(APITestCase):
    url = "/tasks/reorder/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.outsider = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col1 = Column.objects.create(board=self.board, title="Todo", order=0)
        self.col2 = Column.objects.create(board=self.board, title="Done", order=1)
        self.task1 = Task.objects.create(board=self.board, column=self.col1, title="T1", order=1)
        self.task2 = Task.objects.create(board=self.board, column=self.col1, title="T2", order=2)
        self.client.force_authenticate(user=self.user)

    def test_reorder_tasks(self):
        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "order": 3.0}, {"id": self.task2.pk, "order": 1.0}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.assertEqual(self.task1.order, 3.0)
        self.assertEqual(self.task2.order, 1.0)

    def test_reorder_move_column(self):
        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "order": 1.0, "column": self.col2.pk}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.column_id, self.col2.pk)

    def test_reorder_invalid_column(self):
        other_board = Board.objects.create(title="Other", created_by=self.user)
        other_col = Column.objects.create(board=other_board, title="Col", order=0)
        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "column": other_col.pk}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_invalid_data(self):
        response = self.client.post(self.url, [{"wrong": "data"}], format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_nonexistent_task(self):
        response = self.client.post(
            self.url,
            [{"id": 9999, "order": 1.0}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reorder_forbidden_for_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "order": 5.0}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reorder_archived_task_not_found(self):
        self.task1.archived_at = timezone.now()
        self.task1.save(update_fields=["archived_at"])
        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "order": 5.0}],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reorder_to_duplicate_order_uses_created_at_tiebreaker(self):
        older = timezone.now() - timedelta(minutes=1)
        Task.objects.filter(pk=self.task2.pk).update(created_at=older)

        response = self.client.post(
            self.url,
            [{"id": self.task1.pk, "order": 2.0}],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.assertEqual(self.task1.order, self.task2.order)

        ordered = list(Task.objects.filter(column=self.col1).values_list("pk", flat=True))
        self.assertEqual(ordered, [self.task2.pk, self.task1.pk])


class MyTasksTests(APITestCase):
    url = "/tasks/my/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.task1 = Task.objects.create(board=self.board, column=self.col, title="My Task")
        self.task2 = Task.objects.create(board=self.board, column=self.col, title="Another")
        self.client.force_authenticate(user=self.user)

    def test_my_tasks_returns_user_boards(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(all("board_title" in t for t in response.data))

    def test_my_tasks_excludes_other_boards(self):
        other_board = Board.objects.create(title="Other", created_by=self.other)
        Task.objects.create(board=other_board, title="Hidden")
        response = self.client.get(self.url)
        titles = [t["title"] for t in response.data]
        self.assertNotIn("Hidden", titles)

    def test_my_tasks_search_filter(self):
        response = self.client.get(self.url, {"search": "My Task"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "My Task")

    def test_my_tasks_search_no_results(self):
        response = self.client.get(self.url, {"search": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_my_tasks_excludes_archived(self):
        self.task1.archived_at = timezone.now()
        self.task1.save(update_fields=["archived_at"])
        response = self.client.get(self.url)
        titles = [t["title"] for t in response.data]
        self.assertNotIn("My Task", titles)

    def test_my_tasks_includes_member_board(self):
        member_board = Board.objects.create(title="Member Board", created_by=self.other)
        BoardMember.objects.create(board=member_board, user=self.user)
        Task.objects.create(board=member_board, title="Member Task")
        response = self.client.get(self.url)
        titles = [t["title"] for t in response.data]
        self.assertIn("Member Task", titles)


class TaskDuplicateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.outsider = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.task = Task.objects.create(
            board=self.board, column=self.col, title="Original",
            description="Desc", priority="high",
        )
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/tasks/{pk}/duplicate/"

    def test_duplicate_task(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        self.task.labels.add(label)
        Subtask.objects.create(task=self.task, title="Sub 1", done=True)
        response = self.client.post(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Original (copy)")
        self.assertEqual(response.data["priority"], "high")
        self.assertEqual(response.data["subtask_count"], 1)
        self.assertEqual(response.data["subtask_done_count"], 0)
        self.assertEqual(len(response.data["labels"]), 1)

    def test_duplicate_not_found(self):
        response = self.client.post(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_archived_not_found(self):
        self.task.archived_at = timezone.now()
        self.task.save(update_fields=["archived_at"])
        response = self.client.post(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_forbidden_for_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_viewer_forbidden(self):
        viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=viewer, role="viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.post(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TaskHistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.outsider = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.task = Task.objects.create(board=self.board, column=self.col, title="Task")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/tasks/{pk}/history/"

    def test_history_returns_entries(self):
        from activity_api.helpers import log_activity
        log_activity(self.board, self.user, "created", "task", self.task.title, task=self.task)
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["action"], "created")

    def test_history_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_history_outsider_denied(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_history_archived_task_accessible(self):
        from activity_api.helpers import log_activity
        log_activity(self.board, self.user, "deleted", "task", self.task.title, task=self.task)
        self.task.archived_at = timezone.now()
        self.task.save(update_fields=["archived_at"])
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaskWorkloadTests(APITestCase):
    url = "/tasks/workload/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.contact = Contact.objects.create(owner=self.user, first_name="A", last_name="B", email="a@example.com")
        self.client.force_authenticate(user=self.user)

    def test_workload_returns_structure(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("contacts", response.data)
        self.assertIn("tasks", response.data)

    def test_workload_includes_assigned_tasks(self):
        task = Task.objects.create(board=self.board, column=self.col, title="Work", priority="high")
        task.assignees.add(self.contact)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_titles = [t["title"] for t in response.data["tasks"]]
        self.assertIn("Work", task_titles)
        t = response.data["tasks"][0]
        self.assertEqual(t["priority"], "high")
        self.assertIn(self.contact.pk, t["assigned_to"])
        self.assertEqual(t["board_title"], "Board")

    def test_workload_excludes_unassigned_tasks(self):
        Task.objects.create(board=self.board, column=self.col, title="Unassigned")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["tasks"]), 0)

    def test_workload_excludes_archived_tasks(self):
        task = Task.objects.create(
            board=self.board, column=self.col, title="Archived",
            archived_at=timezone.now()
        )
        task.assignees.add(self.contact)
        response = self.client.get(self.url)
        task_titles = [t["title"] for t in response.data["tasks"]]
        self.assertNotIn("Archived", task_titles)

    def test_workload_contacts_list(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["contacts"]), 1)
        self.assertEqual(response.data["contacts"][0]["name"], "A B")

    def test_workload_multi_assignee_task_listed_once(self):
        contact2 = Contact.objects.create(owner=self.user, first_name="C", last_name="D", email="c@example.com")
        task = Task.objects.create(board=self.board, column=self.col, title="Shared")
        task.assignees.add(self.contact, contact2)
        response = self.client.get(self.url)
        shared = [t for t in response.data["tasks"] if t["title"] == "Shared"]
        self.assertEqual(len(shared), 1)
        self.assertCountEqual(shared[0]["assigned_to"], [self.contact.pk, contact2.pk])
