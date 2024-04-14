from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .utils import generate_access_token


User = get_user_model()


class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        valid_registration_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
        }
        response = self.client.post(
            reverse("api:register"), valid_registration_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            User.objects.filter(username=valid_registration_data["username"]).exists()
        )

    def test_user_registration_failure(self):
        
        invalid_registration_data = [
            {
                "username": "",
                "email": "testuser@example.com",
                "password": "testpassword",
            },
            {
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "",
            },
            {
                "username": "testuser",
                "email": "testusermail",
                "password": "testpassword",
            },
        ]
        for data in invalid_registration_data:
            response = self.client.post(reverse("api:register"), data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=data["username"]).exists())


class UserProfileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="testuser", password="testpassword")
        self.access_token = generate_access_token(self.user)

    def test_authenticated_user_profile_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_unauthenticated_user_profile_view(self):
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
