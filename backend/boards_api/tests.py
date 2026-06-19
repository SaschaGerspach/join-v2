from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from columns_api.models import Column
from tasks_api.models import Task
from .models import Board, BoardFavorite, BoardMember

User = get_user_model()


class BoardListTests(APITestCase):
    url = "/boards/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_own_boards(self):
        Board.objects.create(title="My Board", created_by=self.user)
        Board.objects.create(title="Other Board", created_by=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "My Board")

    def test_create_board(self):
        response = self.client.post(self.url, {"title": "New Board"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Board")
        self.assertEqual(Board.objects.count(), 1)

    def test_create_board_creates_default_columns(self):
        self.client.post(self.url, {"title": "New Board"}, format="json")
        board = Board.objects.first()
        columns = list(Column.objects.filter(board=board).order_by("order").values_list("title", flat=True))
        self.assertEqual(columns, settings.DEFAULT_BOARD_COLUMNS)

    def test_create_board_missing_title(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="My Board", created_by=self.user)
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/boards/{pk}/"

    def test_get_board(self):
        response = self.client.get(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "My Board")

    def test_get_board_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_board(self):
        response = self.client.patch(self.url(self.board.pk), {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")

    def test_patch_other_board_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.url(self.board.pk), {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_board(self):
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 0)

    def test_delete_other_board_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_board_invalid_color(self):
        response = self.client.patch(self.url(self.board.pk), {"color": "not-a-color"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_board_valid_color(self):
        response = self.client.patch(self.url(self.board.pk), {"color": "#ff5733"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["color"], "#ff5733")


class AdminBoardAccessTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", is_superuser=True)
        self.board = Board.objects.create(title="Owner Board", created_by=self.owner)
        self.client.force_authenticate(user=self.admin)

    def test_admin_sees_all_boards(self):
        response = self.client.get("/boards/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Owner Board")

    def test_admin_can_patch_any_board(self):
        response = self.client.patch(f"/boards/{self.board.pk}/", {"title": "Admin Edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Admin Edit")

    def test_admin_can_delete_any_board(self):
        response = self.client.delete(f"/boards/{self.board.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 0)

    def test_plain_staff_cannot_access_others_board(self):
        staff = User.objects.create_user(email="staff@example.com", password="pass", is_staff=True)
        self.client.force_authenticate(user=staff)
        self.assertEqual(self.client.get(f"/boards/{self.board.pk}/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(self.client.get("/boards/").data["results"]), 0)

    def test_superuser_cross_board_access_is_audited(self):
        from audit_api.models import AuditLog
        self.client.get(f"/boards/{self.board.pk}/")
        self.assertTrue(
            AuditLog.objects.filter(user=self.admin, event_type="superuser_board_access").exists()
        )

    def test_owner_access_is_not_audited_as_superuser(self):
        from audit_api.models import AuditLog
        self.client.force_authenticate(user=self.owner)
        self.client.get(f"/boards/{self.board.pk}/")
        self.assertFalse(
            AuditLog.objects.filter(event_type="superuser_board_access").exists()
        )


class BoardLeaveTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.member = User.objects.create_user(email="member@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.board = Board.objects.create(title="Team Board", created_by=self.owner)
        BoardMember.objects.create(board=self.board, user=self.member)

    def url(self, pk):
        return f"/boards/{pk}/members/leave/"

    def test_member_can_leave(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BoardMember.objects.filter(board=self.board, user=self.member).exists())

    def test_owner_cannot_leave(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_gets_404(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_board_gets_404(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BoardFavoriteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="My Board", created_by=self.user)
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/boards/{pk}/favorite/"

    def test_favorite_board(self):
        response = self.client.post(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BoardFavorite.objects.filter(board=self.board, user=self.user).exists())

    def test_favorite_idempotent(self):
        self.client.post(self.url(self.board.pk))
        response = self.client.post(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BoardFavorite.objects.filter(board=self.board, user=self.user).count(), 1)

    def test_unfavorite_board(self):
        BoardFavorite.objects.create(board=self.board, user=self.user)
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BoardFavorite.objects.filter(board=self.board, user=self.user).exists())

    def test_unfavorite_not_favorited(self):
        response = self.client.delete(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_favorite_nonexistent_board(self):
        response = self.client.post(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_favorite(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.url(self.board.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_board_list_shows_is_favorite(self):
        BoardFavorite.objects.create(board=self.board, user=self.user)
        response = self.client.get("/boards/")
        self.assertTrue(response.data["results"][0]["is_favorite"])

    def test_favorites_sorted_first(self):
        board2 = Board.objects.create(title="AAA Board", created_by=self.user)
        BoardFavorite.objects.create(board=board2, user=self.user)
        response = self.client.get("/boards/")
        titles = [b["title"] for b in response.data["results"]]
        self.assertEqual(titles[0], "AAA Board")


class BoardExportCSVTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.board = Board.objects.create(title="My Board", created_by=self.user)
        self.col = Column.objects.create(board=self.board, title="To do", order=0)
        Task.objects.create(board=self.board, column=self.col, title="Task 1", priority="high")
        Task.objects.create(board=self.board, column=self.col, title="Task 2", priority="low")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/boards/{pk}/export/csv/"

    def test_export_csv(self):
        response = self.client.get(self.url(self.board.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", response["Content-Disposition"])
        content = response.content.decode()
        self.assertIn("Task 1", content)
        self.assertIn("Task 2", content)
        self.assertIn("Title,Column,Priority", content)

    def test_export_excludes_archived(self):
        from django.utils import timezone
        Task.objects.create(
            board=self.board, column=self.col, title="Archived Task",
            archived_at=timezone.now(),
        )
        response = self.client.get(self.url(self.board.pk))
        content = response.content.decode()
        self.assertNotIn("Archived Task", content)

    def test_outsider_gets_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url(self.board.pk))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_board_404(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, 404)


class BoardMemberRoleTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin_user = User.objects.create_user(email="admin@example.com", password="pass")
        self.editor_user = User.objects.create_user(email="editor@example.com", password="pass")
        self.viewer_user = User.objects.create_user(email="viewer@example.com", password="pass")
        self.board = Board.objects.create(title="Team Board", created_by=self.owner)
        BoardMember.objects.create(board=self.board, user=self.admin_user, role="admin")
        BoardMember.objects.create(board=self.board, user=self.editor_user, role="editor")
        BoardMember.objects.create(board=self.board, user=self.viewer_user, role="viewer")
        self.col = Column.objects.create(board=self.board, title="Todo", order=0)

    def test_members_list_includes_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/boards/{self.board.pk}/members/")
        self.assertEqual(response.status_code, 200)
        roles = {m["email"]: m["role"] for m in response.data}
        self.assertEqual(roles["admin@example.com"], "admin")
        self.assertEqual(roles["editor@example.com"], "editor")
        self.assertEqual(roles["viewer@example.com"], "viewer")

    def test_owner_can_change_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/boards/{self.board.pk}/members/{self.editor_user.pk}/",
            {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "admin")

    def test_admin_can_change_role(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f"/boards/{self.board.pk}/members/{self.editor_user.pk}/",
            {"role": "viewer"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "viewer")

    def test_editor_cannot_change_role(self):
        self.client.force_authenticate(user=self.editor_user)
        response = self.client.patch(
            f"/boards/{self.board.pk}/members/{self.viewer_user.pk}/",
            {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_invite(self):
        User.objects.create_user(email="new@example.com", password="pass")
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f"/boards/{self.board.pk}/members/",
            {"email": "new@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_editor_cannot_invite(self):
        User.objects.create_user(email="new2@example.com", password="pass")
        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/boards/{self.board.pk}/members/",
            {"email": "new2@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_create_task(self):
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.post(
            f"/tasks/?board={self.board.pk}",
            {"title": "New task"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_create_task(self):
        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/tasks/?board={self.board.pk}",
            {"title": "New task"}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_viewer_cannot_edit_task(self):
        self.client.force_authenticate(user=self.viewer_user)
        task = Task.objects.create(board=self.board, column=self.col, title="Task")
        response = self.client.patch(f"/tasks/{task.pk}/", {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_invalid_role_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/boards/{self.board.pk}/members/{self.editor_user.pk}/",
            {"role": "superadmin"}, format="json"
        )
        self.assertEqual(response.status_code, 400)


class BoardImportCSVTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        self.board = Board.objects.create(title="My Board", created_by=self.user)
        BoardMember.objects.create(board=self.board, user=self.viewer, role="viewer")
        self.col = Column.objects.create(board=self.board, title="To do", order=0)
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/boards/{pk}/import/csv/"

    def _make_csv(self, content):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile("tasks.csv", content.encode("utf-8"), content_type="text/csv")

    def test_import_basic(self):
        csv_content = "Title,Column,Priority\nTask A,To do,high\nTask B,,low\n"
        response = self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 2)
        self.assertTrue(Task.objects.filter(board=self.board, title="Task A").exists())

    def test_import_creates_new_column(self):
        csv_content = "Title,Column\nTask X,New Column\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertTrue(Column.objects.filter(board=self.board, title="New Column").exists())

    def test_import_creates_labels(self):
        from tasks_api.models import Label
        csv_content = "Title,Labels\nTask X,\"Bug,Feature\"\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        task = Task.objects.get(board=self.board, title="Task X")
        self.assertEqual(task.labels.count(), 2)
        self.assertTrue(Label.objects.filter(board=self.board, name="Bug").exists())

    def test_import_due_date_formats(self):
        csv_content = "Title,Due Date\nTask ISO,2025-06-15\nTask DE,15.06.2025\nTask US,06/15/2025\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        from datetime import date
        for title in ("Task ISO", "Task DE", "Task US"):
            task = Task.objects.get(board=self.board, title=title)
            self.assertEqual(task.due_date, date(2025, 6, 15))

    def test_import_recurrence(self):
        csv_content = "Title,Recurrence\nTask R,weekly\nTask Bad,invalid\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(Task.objects.get(title="Task R").recurrence, "weekly")
        self.assertIsNone(Task.objects.get(title="Task Bad").recurrence)

    def test_import_invalid_priority_defaults_medium(self):
        csv_content = "Title,Priority\nTask P,invalid\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(Task.objects.get(title="Task P").priority, "medium")

    def test_import_skips_empty_titles(self):
        csv_content = "Title\n\nTask Valid\n  \n"
        response = self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.data["imported"], 1)

    def test_import_no_file(self):
        response = self.client.post(self.url(self.board.pk), {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file", response.data["detail"])

    def test_import_file_too_large(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        large = SimpleUploadedFile("big.csv", b"Title\n" + b"x" * (2 * 1024 * 1024), content_type="text/csv")
        response = self.client.post(self.url(self.board.pk), {"file": large}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("too large", response.data["detail"])

    def test_import_missing_title_column(self):
        csv_content = "Name,Column\nTask,To do\n"
        response = self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Title", response.data["detail"])

    def test_import_nonexistent_board_404(self):
        csv_content = "Title\nTask\n"
        response = self.client.post(self.url(9999), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_import_outsider_gets_404(self):
        self.client.force_authenticate(user=self.other)
        csv_content = "Title\nTask\n"
        response = self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_import_viewer_gets_403(self):
        self.client.force_authenticate(user=self.viewer)
        csv_content = "Title\nTask\n"
        response = self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        self.assertEqual(response.status_code, 403)

    def test_import_reuses_existing_column(self):
        csv_content = "Title,Column\nTask X,To do\n"
        self.client.post(self.url(self.board.pk), {"file": self._make_csv(csv_content)}, format="multipart")
        task = Task.objects.get(board=self.board, title="Task X")
        self.assertEqual(task.column, self.col)
        self.assertEqual(Column.objects.filter(board=self.board, title__iexact="to do").count(), 1)

    def test_import_non_utf8_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        bad_file = SimpleUploadedFile("bad.csv", b"\x80\x81\x82\x83", content_type="text/csv")
        response = self.client.post(self.url(self.board.pk), {"file": bad_file}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("UTF-8", response.data["detail"])
