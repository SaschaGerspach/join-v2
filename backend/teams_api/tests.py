from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Team, TeamMember

User = get_user_model()


class TeamListTests(APITestCase):
    url = "/teams/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_own_teams(self):
        Team.objects.create(name="My Team", created_by=self.user)
        Team.objects.create(name="Other Team", created_by=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "My Team")

    def test_list_includes_teams_as_member(self):
        team = Team.objects.create(name="Shared Team", created_by=self.other)
        TeamMember.objects.create(team=team, user=self.user, role=TeamMember.Role.MEMBER)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Shared Team")

    def test_list_no_duplicates(self):
        team = Team.objects.create(name="My Team", created_by=self.user)
        TeamMember.objects.create(team=team, user=self.user, role=TeamMember.Role.ADMIN)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)

    def test_create_team(self):
        response = self.client.post(self.url, {"name": "New Team"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Team")
        self.assertTrue(response.data["is_owner"])
        self.assertEqual(response.data["member_count"], 1)
        self.assertEqual(Team.objects.count(), 1)

    def test_create_team_missing_name(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_team_blank_name(self):
        response = self.client.post(self.url, {"name": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TeamDetailTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin_user = User.objects.create_user(email="admin@example.com", password="pass")
        self.member_user = User.objects.create_user(email="member@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.team = Team.objects.create(name="Test Team", created_by=self.owner)
        TeamMember.objects.create(team=self.team, user=self.admin_user, role=TeamMember.Role.ADMIN)
        TeamMember.objects.create(team=self.team, user=self.member_user, role=TeamMember.Role.MEMBER)
        self.client.force_authenticate(user=self.owner)

    def url(self, pk):
        return f"/teams/{pk}/"

    def test_get_team_as_owner(self):
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Team")
        self.assertTrue(response.data["is_owner"])

    def test_get_team_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_owner"])

    def test_get_team_as_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_team(self):
        response = self.client.get(self.url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_as_owner(self):
        response = self.client.patch(self.url(self.team.pk), {"name": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Renamed")

    def test_patch_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.url(self.team.pk), {"name": "Admin Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Admin Renamed")

    def test_patch_as_member_denied(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(self.url(self.team.pk), {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_as_outsider_not_found(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.patch(self.url(self.team.pk), {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_empty_name_no_change(self):
        response = self.client.patch(self.url(self.team.pk), {"name": "  "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Team")

    def test_delete_as_owner(self):
        response = self.client.delete(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Team.objects.count(), 0)

    def test_delete_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_member_denied(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_outsider_not_found(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.delete(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StaffTeamAccessTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.staff = User.objects.create_user(email="staff@example.com", password="pass", is_staff=True)
        self.team = Team.objects.create(name="Owner Team", created_by=self.owner)
        self.client.force_authenticate(user=self.staff)

    def test_staff_can_view_any_team(self):
        response = self.client.get(f"/teams/{self.team.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_can_patch_any_team(self):
        response = self.client.patch(f"/teams/{self.team.pk}/", {"name": "Staff Edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Staff Edit")

    def test_staff_can_delete_any_team(self):
        response = self.client.delete(f"/teams/{self.team.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TeamMembersTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", password="pass", first_name="Owner", last_name="User"
        )
        self.admin_user = User.objects.create_user(email="admin@example.com", password="pass")
        self.member_user = User.objects.create_user(email="member@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.team = Team.objects.create(name="Test Team", created_by=self.owner)
        TeamMember.objects.create(team=self.team, user=self.admin_user, role=TeamMember.Role.ADMIN)
        TeamMember.objects.create(team=self.team, user=self.member_user, role=TeamMember.Role.MEMBER)
        self.client.force_authenticate(user=self.owner)

    def url(self, pk):
        return f"/teams/{pk}/members/"

    def test_list_members_includes_owner(self):
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [m["email"] for m in response.data]
        self.assertIn("owner@example.com", emails)
        owner_entry = next(m for m in response.data if m["email"] == "owner@example.com")
        self.assertEqual(owner_entry["role"], "owner")

    def test_list_members_includes_all(self):
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(len(response.data), 3)

    def test_list_members_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_members_as_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url(self.team.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_member_as_owner(self):
        new_user = User.objects.create_user(email="new@example.com", password="pass")
        response = self.client.post(self.url(self.team.pk), {"email": "new@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertEqual(response.data["role"], "member")
        self.assertTrue(TeamMember.objects.filter(team=self.team, user=new_user).exists())

    def test_invite_member_as_admin(self):
        User.objects.create_user(email="new2@example.com", password="pass")
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url(self.team.pk), {"email": "new2@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invite_member_as_regular_member_denied(self):
        User.objects.create_user(email="new3@example.com", password="pass")
        self.client.force_authenticate(user=self.member_user)
        response = self.client.post(self.url(self.team.pk), {"email": "new3@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invite_nonexistent_user(self):
        response = self.client.post(self.url(self.team.pk), {"email": "ghost@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_owner_as_member(self):
        response = self.client.post(self.url(self.team.pk), {"email": "owner@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_already_member_idempotent(self):
        response = self.client.post(self.url(self.team.pk), {"email": "member@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TeamMember.objects.filter(team=self.team, user=self.member_user).count(), 1)

    def test_invite_invalid_email(self):
        response = self.client.post(self.url(self.team.pk), {"email": "not-an-email"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_missing_email(self):
        response = self.client.post(self.url(self.team.pk), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_email_case_insensitive(self):
        User.objects.create_user(email="case@example.com", password="pass")
        response = self.client.post(self.url(self.team.pk), {"email": "CASE@Example.COM"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TeamMemberDetailTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.admin_user = User.objects.create_user(email="admin@example.com", password="pass")
        self.member_user = User.objects.create_user(email="member@example.com", password="pass")
        self.other_member = User.objects.create_user(email="other@example.com", password="pass")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass")
        self.team = Team.objects.create(name="Test Team", created_by=self.owner)
        TeamMember.objects.create(team=self.team, user=self.admin_user, role=TeamMember.Role.ADMIN)
        TeamMember.objects.create(team=self.team, user=self.member_user, role=TeamMember.Role.MEMBER)
        TeamMember.objects.create(team=self.team, user=self.other_member, role=TeamMember.Role.MEMBER)
        self.client.force_authenticate(user=self.owner)

    def url(self, team_pk, user_pk):
        return f"/teams/{team_pk}/members/{user_pk}/"

    def test_update_role_to_admin(self):
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "admin")

    def test_update_role_to_member(self):
        response = self.client.patch(
            self.url(self.team.pk, self.admin_user.pk), {"role": "member"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "member")

    def test_update_role_invalid_value(self):
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": "superadmin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "member")

    def test_update_role_empty_string(self):
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": ""}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "member")

    def test_update_role_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_role_as_member_denied(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(
            self.url(self.team.pk, self.other_member.pk), {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_role_as_outsider_not_found(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": "admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_member_as_owner(self):
        response = self.client.delete(self.url(self.team.pk, self.member_user.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TeamMember.objects.filter(team=self.team, user=self.member_user).exists())

    def test_remove_member_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.url(self.team.pk, self.member_user.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_remove_member_as_regular_member_denied(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.url(self.team.pk, self.other_member.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_nonexistent_member(self):
        response = self.client.delete(self.url(self.team.pk, 9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_member_from_nonexistent_team(self):
        response = self.client.delete(self.url(9999, self.member_user.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_response_fields(self):
        response = self.client.patch(
            self.url(self.team.pk, self.member_user.pk), {"role": "member"}, format="json"
        )
        self.assertIn("user_id", response.data)
        self.assertIn("email", response.data)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)
        self.assertIn("role", response.data)
