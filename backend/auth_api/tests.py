from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class RegisterViewTests(APITestCase):
    url = "/auth/register/"

    def test_register_success(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "password": "securepass123",
            "first_name": "Max",
            "last_name": "Mustermann",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_register_missing_email(self):
        response = self.client.post(self.url, {"password": "securepass123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_password(self):
        response = self.client.post(self.url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="test@example.com", password="pass")
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "password": "otherpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LoginViewTests(APITestCase):
    url = "/auth/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
        )
        self.user.is_verified = True
        self.user.save()

    def test_login_success(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "password": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        response = self.client.post(self.url, {
            "email": "unknown@example.com",
            "password": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):
    url = "/auth/logout/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
        )

    def test_logout_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MeViewTests(APITestCase):
    url = "/auth/me/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
        )

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["id"], self.user.pk)

    def test_me_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SessionListTests(APITestCase):
    url = "/auth/sessions/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.user.is_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def _create_refresh_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        return RefreshToken.for_user(user)

    def test_list_sessions(self):
        self._create_refresh_token(self.user)
        self._create_refresh_token(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_list_sessions_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_has_expected_fields(self):
        self._create_refresh_token(self.user)
        response = self.client.get(self.url)
        session = response.data[0]
        self.assertIn("id", session)
        self.assertIn("created_at", session)
        self.assertIn("expires_at", session)
        self.assertIn("is_current", session)

    def test_sessions_only_own(self):
        other = User.objects.create_user(email="other@example.com", password="pass")
        self._create_refresh_token(other)
        self._create_refresh_token(self.user)
        response = self.client.get(self.url)
        for session in response.data:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            token = OutstandingToken.objects.get(pk=session["id"])
            self.assertEqual(token.user, self.user)


class SessionRevokeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def _create_refresh_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        return RefreshToken.for_user(user)

    def test_revoke_session(self):
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        token = self._create_refresh_token(self.user)
        outstanding = OutstandingToken.objects.get(jti=token["jti"])
        response = self.client.delete(f"/auth/sessions/{outstanding.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding).exists())

    def test_revoke_nonexistent_session(self):
        response = self.client.delete("/auth/sessions/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_other_users_session(self):
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        other = User.objects.create_user(email="other@example.com", password="pass")
        token = self._create_refresh_token(other)
        outstanding = OutstandingToken.objects.get(jti=token["jti"])
        response = self.client.delete(f"/auth/sessions/{outstanding.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SessionRevokeAllTests(APITestCase):
    url = "/auth/sessions/revoke-all/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def _create_refresh_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        return RefreshToken.for_user(user)

    def test_revoke_all_sessions(self):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        self._create_refresh_token(self.user)
        self._create_refresh_token(self.user)
        self._create_refresh_token(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertGreaterEqual(BlacklistedToken.objects.count(), 2)

    def test_revoke_all_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AvatarUploadTests(APITestCase):
    url = "/auth/avatar/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def _make_image(self, width=100, height=100, fmt="PNG", name="test.png"):
        from PIL import Image
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = Image.new("RGB", (width, height), color="red")
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        content_type = f"image/{fmt.lower()}"
        return SimpleUploadedFile(name, buf.read(), content_type=content_type)

    def test_upload_avatar(self):
        image = self._make_image()
        response = self.client.post(self.url, {"avatar": image}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertIn("avatar_url", response.data)
        self.assertIsNotNone(response.data["avatar_url"])

    def test_upload_large_image_resized(self):
        image = self._make_image(width=512, height=512)
        response = self.client.post(self.url, {"avatar": image}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_upload_no_file(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file", response.data["detail"])

    def test_upload_too_large(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile("big.png", b"x" * (3 * 1024 * 1024), content_type="image/png")
        response = self.client.post(self.url, {"avatar": big}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("too large", response.data["detail"])

    def test_upload_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        txt = SimpleUploadedFile("file.txt", b"not an image", content_type="text/plain")
        response = self.client.post(self.url, {"avatar": txt}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.data["detail"])

    def test_delete_avatar(self):
        image = self._make_image()
        self.client.post(self.url, {"avatar": image}, format="multipart")
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["avatar_url"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_delete_avatar_when_none(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["avatar_url"])

    def test_upload_replaces_existing(self):
        img1 = self._make_image()
        self.client.post(self.url, {"avatar": img1}, format="multipart")
        img2 = self._make_image(width=50, height=50)
        response = self.client.post(self.url, {"avatar": img2}, format="multipart")
        self.assertEqual(response.status_code, 200)

    def test_upload_unauthenticated(self):
        self.client.force_authenticate(user=None)
        image = self._make_image()
        response = self.client.post(self.url, {"avatar": image}, format="multipart")
        self.assertEqual(response.status_code, 401)


class PasswordResetRequestTests(APITestCase):
    url = "/auth/password-reset/"

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="oldpass123")

    def test_request_with_existing_email(self):
        from unittest.mock import patch
        with patch("auth_api.views.password_reset.send_mail_async") as mock_mail:
            response = self.client.post(self.url, {"email": "test@example.com"})
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock_mail.assert_called_once()

    def test_request_with_unknown_email(self):
        from unittest.mock import patch
        with patch("auth_api.views.password_reset.send_mail_async") as mock_mail:
            response = self.client.post(self.url, {"email": "unknown@example.com"})
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock_mail.assert_not_called()

    def test_request_invalid_email(self):
        response = self.client.post(self.url, {"email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_missing_email(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_email_case_insensitive(self):
        from unittest.mock import patch
        with patch("auth_api.views.password_reset.send_mail_async") as mock_mail:
            response = self.client.post(self.url, {"email": "Test@Example.COM"})
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock_mail.assert_called_once()


class PasswordResetConfirmTests(APITestCase):
    url = "/auth/password-reset/confirm/"

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="oldpass123")

    def _get_uid_token(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return uid, token

    def test_confirm_success(self):
        uid, token = self._get_uid_token()
        response = self.client.post(self.url, {
            "uid": uid,
            "token": token,
            "password": "newpass12345",
        })
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass12345"))

    def test_confirm_invalid_uid(self):
        _, token = self._get_uid_token()
        response = self.client.post(self.url, {
            "uid": "invalid",
            "token": token,
            "password": "newpass12345",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_invalid_token(self):
        uid, _ = self._get_uid_token()
        response = self.client.post(self.url, {
            "uid": uid,
            "token": "invalid-token",
            "password": "newpass12345",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_token_reuse(self):
        uid, token = self._get_uid_token()
        self.client.post(self.url, {"uid": uid, "token": token, "password": "newpass12345"})
        response = self.client.post(self.url, {"uid": uid, "token": token, "password": "anotherpass123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_weak_password(self):
        uid, token = self._get_uid_token()
        response = self.client.post(self.url, {
            "uid": uid,
            "token": token,
            "password": "12345678",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_missing_fields(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
