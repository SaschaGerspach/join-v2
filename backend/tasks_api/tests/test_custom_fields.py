
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from columns_api.models import Column
from ..models import Task, CustomField, TaskFieldValue

User = get_user_model()


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

    def test_duplicate_custom_field_name_rejected(self):
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

    def test_set_field_value_rejects_invalid_select_option(self):
        field = CustomField.objects.create(board=self.board, name="Size", field_type="select", options=["S", "M", "L"])
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [{"field_id": field.pk, "value": "XXL"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TaskFieldValue.objects.filter(task=task, field=field).exists())

    def test_set_field_value_rejects_invalid_number(self):
        field = CustomField.objects.create(board=self.board, name="Points", field_type="number")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [{"field_id": field.pk, "value": "abc"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_field_value_rejects_invalid_date(self):
        field = CustomField.objects.create(board=self.board, name="Deadline", field_type="date")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [{"field_id": field.pk, "value": "31/12/2026"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_field_value_accepts_valid_typed_values(self):
        select_field = CustomField.objects.create(board=self.board, name="Size", field_type="select", options=["S", "M"])
        number_field = CustomField.objects.create(board=self.board, name="Points", field_type="number")
        date_field = CustomField.objects.create(board=self.board, name="Deadline", field_type="date")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [
                {"field_id": select_field.pk, "value": "M"},
                {"field_id": number_field.pk, "value": "3.5"},
                {"field_id": date_field.pk, "value": "2026-12-31"},
            ]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["values"]), 3)

    def test_set_field_values_is_atomic_on_invalid(self):
        good = CustomField.objects.create(board=self.board, name="Sprint", field_type="text")
        bad = CustomField.objects.create(board=self.board, name="Points", field_type="number")
        task = Task.objects.create(board=self.board, column=self.col, title="Task 1")
        response = self.client.put(
            f"/tasks/{task.pk}/fields/",
            {"values": [
                {"field_id": good.pk, "value": "Sprint 5"},
                {"field_id": bad.pk, "value": "not-a-number"},
            ]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TaskFieldValue.objects.filter(task=task).exists())
