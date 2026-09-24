from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board, BoardMember

User = get_user_model()


class UserListTests(APITestCase):
    url = "/users/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        self.other = User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        board = Board.objects.create(title="Shared", created_by=self.user)
        BoardMember.objects.create(board=board, user=self.other)
        self.client.force_authenticate(user=self.user)

    def test_list_returns_co_members(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "b@example.com")

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass", first_name="Anna", last_name="A")
        self.other = User.objects.create_user(email="b@example.com", password="pass", first_name="Bob", last_name="B")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/users/{pk}/"

    def test_get_user(self):
        response = self.client.get(self.url(self.user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "a@example.com")

    def test_get_user_not_found(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_profile(self):
        response = self.client.patch(self.url(self.user.pk), {"first_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_patch_other_profile_forbidden(self):
        response = self.client.patch(self.url(self.other.pk), {"first_name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_email_requires_staff(self):
        response = self.client.patch(self.url(self.user.pk), {"email": "new@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "a@example.com")

    def test_patch_email_duplicate_rejected(self):
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(self.url(self.user.pk), {"email": "b@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "a@example.com")

    def test_delete_own_account(self):
        response = self.client.delete(self.url(self.user.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_delete_other_account_forbidden(self):
        response = self.client.delete(self.url(self.other.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_admin(self):
        self.user.is_staff = True
        self.user.save()
        target = User.objects.create_user(email="target@example.com", password="pass")
        response = self.client.delete(self.url(target.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.get(pk=target.pk).is_active)

    def test_password_change_requires_current_password(self):
        response = self.client.patch(self.url(self.user.pk), {"password": "newsecret123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.patch(
            self.url(self.user.pk), {"password": "newsecret123", "current_password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("pass"))

    def test_password_change_revokes_sessions_and_issues_new_refresh_token(self):
        from django.conf import settings
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        from rest_framework_simplejwt.tokens import RefreshToken

        old = RefreshToken.for_user(self.user)
        response = self.client.patch(
            self.url(self.user.pk), {"password": "newsecret123", "current_password": "pass"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecret123"))
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old["jti"]).exists())
        new_jti = RefreshToken(response.cookies[settings.REFRESH_COOKIE_NAME].value)["jti"]
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=new_jti).exists())

    def test_admin_cannot_set_password_of_other_user(self):
        self.user.is_superuser = True
        self.user.save()
        response = self.client.patch(
            self.url(self.other.pk), {"password": "newsecret123", "current_password": "pass"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other.refresh_from_db()
        self.assertTrue(self.other.check_password("pass"))

    def test_staff_cannot_modify_superuser(self):
        self.user.is_staff = True
        self.user.save()
        root = User.objects.create_user(email="root@example.com", password="pass", is_superuser=True)
        response = self.client.patch(self.url(root.pk), {"email": "attacker@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.url(root.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        root.refresh_from_db()
        self.assertEqual(root.email, "root@example.com")
        self.assertTrue(root.is_active)

    def test_staff_cannot_modify_other_staff(self):
        self.user.is_staff = True
        self.user.save()
        admin = User.objects.create_user(email="admin2@example.com", password="pass", is_staff=True)
        response = self.client.patch(self.url(admin.pk), {"first_name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_modify_staff(self):
        self.user.is_superuser = True
        self.user.save()
        admin = User.objects.create_user(email="admin2@example.com", password="pass", is_staff=True)
        response = self.client.patch(self.url(admin.pk), {"first_name": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_transfers_board_to_member(self):
        self.user.is_staff = True
        self.user.save()
        target = User.objects.create_user(email="target@example.com", password="pass")
        board = Board.objects.create(title="Team", created_by=target)
        BoardMember.objects.create(board=board, user=self.other)
        self.client.delete(self.url(target.pk))
        board.refresh_from_db()
        self.assertEqual(board.created_by, self.other)
        self.assertFalse(BoardMember.objects.filter(board=board, user=self.other).exists())

    def test_delete_preserves_board_without_members(self):
        self.user.is_staff = True
        self.user.save()
        target = User.objects.create_user(email="target@example.com", password="pass")
        board = Board.objects.create(title="Solo", created_by=target)
        self.client.delete(self.url(target.pk))
        board.refresh_from_db()
        self.assertTrue(board.title.startswith("[Deleted User]"))

    def test_delete_removes_memberships(self):
        self.user.is_staff = True
        self.user.save()
        target = User.objects.create_user(email="target@example.com", password="pass")
        board = Board.objects.create(title="Other", created_by=self.other)
        BoardMember.objects.create(board=board, user=target)
        self.client.delete(self.url(target.pk))
        self.assertFalse(BoardMember.objects.filter(user=target).exists())


class DeleteAccountServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="leaver@example.com", password="pass", first_name="Lea")
        self.other = User.objects.create_user(email="stayer@example.com", password="pass")

    def test_team_is_handed_to_earliest_member(self):
        from teams_api.models import Team, TeamMember

        from .services import delete_account

        team = Team.objects.create(name="Crew", created_by=self.user)
        TeamMember.objects.create(team=team, user=self.other)
        delete_account(self.user)
        team.refresh_from_db()
        self.assertEqual(team.created_by, self.other)
        self.assertFalse(TeamMember.objects.filter(team=team, user=self.other).exists())

    def test_team_without_members_is_deleted(self):
        from teams_api.models import Team

        from .services import delete_account

        Team.objects.create(name="Solo", created_by=self.user)
        delete_account(self.user)
        self.assertFalse(Team.objects.filter(name="Solo").exists())

    def test_user_is_anonymized_and_deactivated(self):
        from .services import delete_account

        delete_account(self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.email.endswith("@anonymized.local"))
        self.assertEqual(self.user.first_name, "Deleted")
        self.assertFalse(self.user.has_usable_password())

    def test_all_refresh_tokens_are_revoked(self):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        from rest_framework_simplejwt.tokens import RefreshToken

        from .services import delete_account

        RefreshToken.for_user(self.user)
        RefreshToken.for_user(self.user)
        delete_account(self.user)
        outstanding = OutstandingToken.objects.filter(user=self.user)
        self.assertEqual(outstanding.count(), 2)
        self.assertEqual(BlacklistedToken.objects.filter(token__in=outstanding).count(), 2)
