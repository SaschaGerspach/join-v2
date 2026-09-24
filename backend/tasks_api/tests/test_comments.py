
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from contacts_api.models import Contact
from notifications_api.models import Notification
from ..models import Task, Comment

User = get_user_model()


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
        # A regular member (neither author nor board admin) cannot edit someone else's comment.
        comment = Comment.objects.create(task=self.task, author=self.user, text="X")
        self.client.force_authenticate(user=self.member)
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
        admin = User.objects.create_user(email="admin@example.com", password="pass", is_superuser=True)
        comment = Comment.objects.create(task=self.task, author=self.user, text="Original")
        self.client.force_authenticate(user=admin)
        response = self.client.patch(self.detail_url(comment.pk), {"text": "Admin Edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Admin Edit")

    def test_admin_can_delete_others_comment(self):
        admin = User.objects.create_user(email="admin2@example.com", password="pass", is_superuser=True)
        comment = Comment.objects.create(task=self.task, author=self.user, text="To Delete")
        self.client.force_authenticate(user=admin)
        response = self.client.delete(self.detail_url(comment.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_comment_notifies_assignee_and_prior_author_but_not_actor(self):
        prior = User.objects.create_user(email="p@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=prior)
        Comment.objects.create(task=self.task, author=prior, text="Earlier")
        self.task.assignees.add(
            Contact.objects.create(owner=self.user, first_name="M", last_name="M", email="M@Example.com")
        )

        response = self.client.post(self.list_url(), {"text": "Update"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notified = set(
            Notification.objects.filter(type=Notification.Type.COMMENT).values_list("recipient_id", flat=True)
        )
        self.assertEqual(notified, {self.member.pk, prior.pk})

    def test_comment_notification_queries_independent_of_assignee_count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def query_count():
            with CaptureQueriesContext(connection) as ctx:
                self.client.post(self.list_url(), {"text": "Ping"}, format="json")
            return len(ctx.captured_queries)

        def add_external_assignee(i):
            self.task.assignees.add(
                Contact.objects.create(owner=self.user, first_name="E", last_name=str(i), email=f"ext{i}@example.com")
            )

        add_external_assignee(0)
        query_count()
        baseline = query_count()
        for i in range(1, 4):
            add_external_assignee(i)
        self.assertEqual(query_count(), baseline)

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
