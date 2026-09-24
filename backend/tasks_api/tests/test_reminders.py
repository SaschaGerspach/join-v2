from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from boards_api.models import Board
from contacts_api.models import Contact
from notifications_api.models import Notification
from ..models import Task

User = get_user_model()


class DueDateReminderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.board = Board.objects.create(title="Board", created_by=self.user)
        self.contact = Contact.objects.create(
            owner=self.user, first_name="A", last_name="B", email="a@example.com"
        )

    def test_reminder_sent_for_task_due_tomorrow(self):
        from ..tasks import send_due_date_reminders

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
        from ..tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Overdue",
            due_date=timezone.now().date() - timedelta(days=1),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_reminder_for_far_future(self):
        from ..tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Far Away",
            due_date=timezone.now().date() + timedelta(days=10),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_duplicate_reminder(self):
        from ..tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Due Soon",
            due_date=timezone.now().date() + timedelta(days=1),
        )
        task.assignees.add(self.contact)
        send_due_date_reminders()
        count = send_due_date_reminders()
        self.assertEqual(count, 0)

    def test_no_reminder_for_archived_task(self):
        from ..tasks import send_due_date_reminders

        task = Task.objects.create(
            board=self.board, title="Archived",
            due_date=timezone.now().date() + timedelta(days=1),
            archived_at=timezone.now(),
        )
        task.assignees.add(self.contact)
        count = send_due_date_reminders()
        self.assertEqual(count, 0)
