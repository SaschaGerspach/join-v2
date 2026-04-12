from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class RegisterViewTests(APITestCase):
    url = "/auth/register"

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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(APITestCase):
    url = "/auth/login"

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
    url = "/auth/logout"

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
        )

    def test_logout_success(self):
        self.client.login(username="test@example.com", password="securepass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MeViewTests(APITestCase):
    url = "/auth/me"

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
        )

    def test_me_authenticated(self):
        self.client.login(username="test@example.com", password="securepass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["id"], self.user.pk)

    def test_me_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
