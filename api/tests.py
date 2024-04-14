import uuid

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.conf import settings

from api.views import refresh_token

from .utils import generate_access_token, generate_refresh_token


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
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.access_token = generate_access_token(self.user)

    def test_authenticated_user_profile_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_unauthenticated_user_profile_view(self):
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_user_login_success(self):
        user_login_data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(
            reverse("api:login"), user_login_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

    def test_invalid_login_attempts(self):
        user_login_data = [
            {},
            {
                "username": "testuser",
                "password": "wrongpassword",
            },
            {
                "username": "nonexistentuser",
                "password": "testpassword",
            },
        ]
        for data in user_login_data:
            response = self.client.post(reverse("api:login"), data, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserLogoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_authenticated_user_logout_success(self):
        generate_refresh_token(self.user)
        refresh_token_data = {"refresh_token": self.user.refresh_token}
        response = self.client.post(
            reverse("api:logout"), refresh_token_data, format="json"
        )
        self.assertEqual(response.data, {"success": "User logged out."})
        self.user.refresh_from_db()
        self.assertEqual(self.user.refresh_token_created_at, None)
        self.assertEqual(self.user.refresh_token_expires_at, None)

    def test_authenticated_user_logout_failed(self):
        generate_refresh_token(self.user)
        refresh_token_expires_at = self.user.refresh_token_expires_at
        refresh_token_data = [
            {},
            {"refresh_token": None},
            {"refresh_token": "NotUUID"},
            {"refresh_token": uuid.uuid4()},
        ]
        response_status = [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]
        for token, expected_status in zip(refresh_token_data, response_status):
            response = self.client.post(reverse("api:logout"), token, format="json")
            self.assertEqual(response.status_code, expected_status)
            self.user.refresh_from_db()
            self.assertEqual(
                refresh_token_expires_at, self.user.refresh_token_expires_at
            )
