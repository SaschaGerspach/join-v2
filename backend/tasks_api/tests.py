from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from columns_api.models import Column
from contacts_api.models import Contact
from notifications_api.models import Notification
from .models import Task, Subtask, Label, Comment, TaskDependency, CustomField, TaskFieldValue, TimeEntry

User = get_user_model()


class TaskListTests(APITestCase):
    url = "/tasks/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
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


class SubtaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.force_authenticate(user=self.user)

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
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.detail_url(subtask.pk), {"done": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_subtask(self):
        subtask = Subtask.objects.create(task=self.task, title="Sub")
        response = self.client.delete(self.detail_url(subtask.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subtask.objects.count(), 0)


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


class CommentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.member = User.objects.create_user(email="m@example.com", password="pass")
        self.outsider = User.objects.create_user(email="x@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        BoardMember.objects.create(board=self.board, user=self.member)
        self.task = Task.objects.create(board=self.board, title="Task")
        self.client.force_authenticate(user=self.user)

    def list_url(self):
        return f"/tasks/{self.task.pk}/comments/"

    def detail_url(self, pk):
        return f"/tasks/{self.task.pk}/comments/{pk}/"

    def test_create_comment(self):
        response = self.client.post(self.list_url(), {"text": "Hello"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Hello")

    def test_list_comments(self):
        Comment.objects.create(task=self.task, author=self.user, text="A")
        Comment.objects.create(task=self.task, author=self.member, text="B")
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_edit_own_comment(self):
        comment = Comment.objects.create(task=self.task, author=self.user, text="Old")
        response = self.client.patch(self.detail_url(comment.pk), {"text": "New"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "New")

    def test_cannot_edit_others_comment(self):
        comment = Comment.objects.create(task=self.task, author=self.member, text="X")
        response = self.client.patch(self.detail_url(comment.pk), {"text": "Y"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_comment(self):
        comment = Comment.objects.create(task=self.task, author=self.user, text="X")
        response = self.client.delete(self.detail_url(comment.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_outsider_cannot_access_comments(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_edit_own_comment_after_removal(self):
        comment = Comment.objects.create(task=self.task, author=self.member, text="X")
        BoardMember.objects.filter(board=self.board, user=self.member).delete()
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(self.detail_url(comment.pk), {"text": "Y"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_edit_others_comment(self):
        admin = User.objects.create_user(email="admin@example.com", password="pass", is_staff=True)
        comment = Comment.objects.create(task=self.task, author=self.user, text="Original")
        self.client.force_authenticate(user=admin)
        response = self.client.patch(self.detail_url(comment.pk), {"text": "Admin Edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Admin Edit")

    def test_admin_can_delete_others_comment(self):
        admin = User.objects.create_user(email="admin2@example.com", password="pass", is_staff=True)
        comment = Comment.objects.create(task=self.task, author=self.user, text="To Delete")
        self.client.force_authenticate(user=admin)
        response = self.client.delete(self.detail_url(comment.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_mention_creates_notification(self):
        from notifications_api.models import Notification

        response = self.client.post(
            self.list_url(),
            {"text": "Hey @m@example.com check this"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mention_notif = Notification.objects.filter(
            recipient=self.member, type=Notification.Type.MENTION
        )
        self.assertEqual(mention_notif.count(), 1)
        self.assertIn("mentioned you", mention_notif.first().message)

    def test_mention_does_not_notify_self(self):
        from notifications_api.models import Notification

        response = self.client.post(
            self.list_url(),
            {"text": "Note to self @a@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(
            Notification.objects.filter(recipient=self.user, type=Notification.Type.MENTION).exists()
        )

    def test_mention_invalid_email_no_notification(self):
        from notifications_api.models import Notification

        response = self.client.post(
            self.list_url(),
            {"text": "Hey @nonexistent@nowhere.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.filter(type=Notification.Type.MENTION).count(), 0)


class TaskArchiveTests(APITestCase):
    archive_url = "/tasks/archive/"

    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.member = User.objects.create_user(email="member@example.com", password="pass")
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", is_staff=True)
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

    def test_list_archive_as_admin(self):
        self.client.force_authenticate(user=self.admin)
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


class AdminAccessTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", is_staff=True)
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
class DueDateReminderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.contact = Contact.objects.create(
            owner=self.user, first_name="A", last_name="B", email="a@example.com"
        )

    def test_reminder_sent_for_task_due_tomorrow(self):
        from .tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Due Soon",
            due_date=timezone.now().date() + timedelta(days=1),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 1)
        notif = Notification.objects.get(recipient=self.user)
        self.assertIn("due tomorrow", notif.message)

    def test_no_reminder_for_past_due_date(self):
        from .tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Overdue",
            due_date=timezone.now().date() - timedelta(days=1),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_reminder_for_far_future(self):
        from .tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Far Away",
            due_date=timezone.now().date() + timedelta(days=10),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_duplicate_reminder(self):
        from .tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Due Soon",
            due_date=timezone.now().date() + timedelta(days=1),
        )
        task.assignees.add(self.contact)
        send_due_date_reminders()
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_reminder_for_archived_task(self):
        from .tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Archived",
            due_date=timezone.now().date() + timedelta(days=1),
            archived_at=timezone.now(),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)


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


class CustomFieldTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.client.force_authenticate(user=self.user)

    def fields_url(self):
        return f"/boards/{self.board.pk}/fields/"

    def field_url(self, pk):
        return f"/boards/{self.board.pk}/fields/{pk}/"

    def test_create_text_field(self):
        response = self.client.post(self.fields_url(), {"name": "Sprint", "field_type": "text"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Sprint")
        self.assertEqual(response.data["field_type"], "text")

    def test_create_select_field_with_options(self):
        response = self.client.post(self.fields_url(), {
            "name": "Size", "field_type": "select", "options": ["S", "M", "L", "XL"]
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["options"], ["S", "M", "L", "XL"])

    def test_list_fields(self):
        CustomField.objects.create(board=self.board, name="F1", field_type="text")
        CustomField.objects.create(board=self.board, name="F2", field_type="number")
        response = self.client.get(self.fields_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_field(self):
        field = CustomField.objects.create(board=self.board, name="Old", field_type="text")
        response = self.client.patch(self.field_url(field.pk), {"name": "New"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "New")

    def test_delete_field(self):
        field = CustomField.objects.create(board=self.board, name="Remove", field_type="text")
        response = self.client.delete(self.field_url(field.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomField.objects.filter(pk=field.pk).exists())

    def test_duplicate_name_rejected(self):
        CustomField.objects.create(board=self.board, name="Sprint", field_type="text")
        response = self.client.post(self.fields_url(), {"name": "Sprint", "field_type": "text"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_create(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.fields_url(), {"name": "X", "field_type": "text"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_set_task_field_values(self):
        field = CustomField.objects.create(board=self.board, name="Sprint", field_type="text")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [{"field_id": field.pk, "value": "Sprint 5"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["values"][0]["value"], "Sprint 5")

    def test_get_task_field_values(self):
        field = CustomField.objects.create(board=self.board, name="Points", field_type="number")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        TaskFieldValue.objects.create(task=task, field=field, value="8")
        response = self.client.get(f"/tasks/{task.pk}/fields/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["values"]), 1)
        self.assertEqual(response.data["values"][0]["value"], "8")


class TimeTrackingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)
        self.task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        self.client.force_authenticate(user=self.user)

    def url(self, task_pk):
        return f"/tasks/{task_pk}/time/"

    def detail_url(self, task_pk, pk):
        return f"/tasks/{task_pk}/time/{pk}/"

    def test_log_time(self):
        response = self.client.post(self.url(self.task.pk), {"duration_minutes": 30, "note": "Research"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["duration_minutes"], 30)
        self.assertEqual(response.data["note"], "Research")
        self.assertEqual(TimeEntry.objects.count(), 1)

    def test_list_time_entries(self):
        TimeEntry.objects.create(task=self.task, user=self.user, duration_minutes=60)
        TimeEntry.objects.create(task=self.task, user=self.user, duration_minutes=30)
        response = self.client.get(self.url(self.task.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_minutes"], 90)
        self.assertEqual(len(response.data["entries"]), 2)

    def test_delete_own_entry(self):
        entry = TimeEntry.objects.create(task=self.task, user=self.user, duration_minutes=15)
        response = self.client.delete(self.detail_url(self.task.pk, entry.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TimeEntry.objects.filter(pk=entry.pk).exists())

    def test_cannot_delete_others_entry(self):
        BoardMember.objects.create(board=self.board, user=self.other)
        entry = TimeEntry.objects.create(task=self.task, user=self.user, duration_minutes=15)
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.detail_url(self.task.pk, entry.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_log_time(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.url(self.task.pk), {"duration_minutes": 10}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_duration_rejected(self):
        response = self.client.post(self.url(self.task.pk), {"duration_minutes": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_max_duration_rejected(self):
        response = self.client.post(self.url(self.task.pk), {"duration_minutes": 1441}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
