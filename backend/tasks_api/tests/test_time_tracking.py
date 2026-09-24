
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember
from columns_api.models import Column
from ..models import Task, TimeEntry

User = get_user_model()


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
