from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from .models import Task, Subtask, Label, Comment

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
