from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification

User = get_user_model()


class NotificationListTests(APITestCase):
    url = "/notifications/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_own_notifications(self):
        Notification.objects.create(recipient=self.user, type="assignment", message="You were assigned")
        Notification.objects.create(recipient=self.other, type="comment", message="Someone else")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["message"], "You were assigned")

    def test_list_ordered_newest_first(self):
        n1 = Notification.objects.create(recipient=self.user, type="assignment", message="First")
        n2 = Notification.objects.create(recipient=self.user, type="comment", message="Second")
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]["id"], n2.pk)
        self.assertEqual(response.data[1]["id"], n1.pk)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_max_50(self):
        for i in range(55):
            Notification.objects.create(recipient=self.user, type="assignment", message=f"N{i}")
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 50)


class NotificationReadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.notification = Notification.objects.create(
            recipient=self.user, type="assignment", message="Test", board_id=1, task_id=1,
        )
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/notifications/{pk}/read/"

    def test_mark_as_read(self):
        self.assertFalse(self.notification.is_read)
        response = self.client.patch(self.url(self.notification.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_as_read_not_found(self):
        response = self.client.patch(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_as_read_other_user(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.url(self.notification.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_as_read_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.url(self.notification.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationReadAllTests(APITestCase):
    url = "/notifications/read-all/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_mark_all_as_read(self):
        Notification.objects.create(recipient=self.user, type="assignment", message="A")
        Notification.objects.create(recipient=self.user, type="comment", message="B")
        Notification.objects.create(recipient=self.other, type="assignment", message="Other")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 0)
        self.assertEqual(self.other.notifications.filter(is_read=False).count(), 1)

    def test_mark_all_as_read_empty(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_all_as_read_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationModelTests(APITestCase):
    def test_create_with_all_fields(self):
        user = User.objects.create_user(email="a@example.com", password="pass")
        n = Notification.objects.create(
            recipient=user, type=Notification.Type.ASSIGNMENT,
            message="Assigned", board_id=5, task_id=10,
        )
        self.assertEqual(n.recipient, user)
        self.assertEqual(n.type, "assignment")
        self.assertFalse(n.is_read)
        self.assertEqual(n.board_id, 5)
        self.assertEqual(n.task_id, 10)
        self.assertIsNotNone(n.created_at)

    def test_create_without_optional_fields(self):
        user = User.objects.create_user(email="a@example.com", password="pass")
        n = Notification.objects.create(
            recipient=user, type=Notification.Type.COMMENT, message="Comment",
        )
        self.assertIsNone(n.board_id)
        self.assertIsNone(n.task_id)

    def test_cascade_delete_user(self):
        user = User.objects.create_user(email="a@example.com", password="pass")
        Notification.objects.create(recipient=user, type="assignment", message="Test")
        self.assertEqual(Notification.objects.count(), 1)
        user.delete()
        self.assertEqual(Notification.objects.count(), 0)
