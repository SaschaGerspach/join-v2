from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Contact

User = get_user_model()


class ContactListTests(APITestCase):
    url = "/contacts/"

    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_list_own_contacts(self):
        Contact.objects.create(owner=self.user, first_name="Anna", last_name="A", email="anna@example.com")
        Contact.objects.create(owner=self.other, first_name="Bob", last_name="B", email="bob@example.com")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_contact(self):
        response = self.client.post(self.url, {
            "first_name": "Max", "last_name": "M", "email": "max@example.com"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "Max")

    def test_create_contact_missing_field(self):
        response = self.client.post(self.url, {"first_name": "Max"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_contact_email(self):
        Contact.objects.create(owner=self.user, first_name="Anna", last_name="A", email="anna@example.com")
        response = self.client.post(self.url, {
            "first_name": "Anna", "last_name": "B", "email": "anna@example.com"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContactDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="pass")
        self.other = User.objects.create_user(email="b@example.com", password="pass")
        self.contact = Contact.objects.create(owner=self.user, first_name="Anna", last_name="A", email="anna@example.com")
        self.client.force_authenticate(user=self.user)

    def url(self, pk):
        return f"/contacts/{pk}/"

    def test_patch_contact(self):
        response = self.client.patch(self.url(self.contact.pk), {"first_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_patch_other_contact_not_found(self):
        other_contact = Contact.objects.create(owner=self.other, first_name="Bob", last_name="B", email="bob@example.com")
        response = self.client.patch(self.url(other_contact.pk), {"first_name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_duplicate_email_rejected(self):
        Contact.objects.create(owner=self.user, first_name="Bob", last_name="B", email="bob@example.com")
        response = self.client.patch(self.url(self.contact.pk), {"email": "bob@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.email, "anna@example.com")

    def test_delete_contact(self):
        response = self.client.delete(self.url(self.contact.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.filter(owner=self.user).count(), 0)
