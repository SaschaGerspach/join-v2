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
