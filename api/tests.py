import uuid
import time

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from api.views import refresh_token

from .utils import generate_access_token, generate_refresh_token


VALID_REG_DATA = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword",
}


User = get_user_model()


class UserCommonTestFunctionality(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=VALID_REG_DATA["username"],
            email=VALID_REG_DATA["email"],
            password=VALID_REG_DATA["password"],
        )


class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        response = self.client.post(
            reverse("api:register"), VALID_REG_DATA, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            User.objects.filter(username=VALID_REG_DATA["username"]).exists()
        )

    def test_user_registration_failure(self):
        invalid_registration_data = [
            {
                "username": "",
                "email": VALID_REG_DATA["email"],
                "password": VALID_REG_DATA["password"],
            },
            {
                "username": VALID_REG_DATA["username"],
                "email": VALID_REG_DATA["email"],
                "password": "",
            },
            {
                "username": VALID_REG_DATA["username"],
                "email": "testusermail",
                "password": VALID_REG_DATA["password"],
            },
        ]
        for data in invalid_registration_data:
            response = self.client.post(reverse("api:register"), data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=data["username"]).exists())


class UserProfileViewTestCase(UserCommonTestFunctionality):
    def test_authenticated_user_profile_view(self):
        access_token = generate_access_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_unauthenticated_user_profile_view(self):
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserLoginTestCase(UserCommonTestFunctionality):
    def test_user_login_success(self):
        user_login_data = {
            "username": VALID_REG_DATA["username"],
            "password": VALID_REG_DATA["password"],
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
                "username": VALID_REG_DATA["username"],
                "password": "wrongpassword",
            },
            {
                "username": "nonexistentuser",
                "password": VALID_REG_DATA["password"],
            },
        ]
        for data in user_login_data:
            response = self.client.post(reverse("api:login"), data, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserLogoutTestCase(UserCommonTestFunctionality):
    def test_authenticated_user_logout_success(self):
        generate_refresh_token(self.user)
        refresh_token_data = {"refresh_token": self.user.refresh_token}
        response = self.client.post(
            reverse("api:logout"), refresh_token_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.refresh_token_created_at, None)
        self.assertEqual(self.user.refresh_token_expires_at, None)

    def test_user_with_invalid_token_failed_logout(self):
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


class UserRefreshTestCase(UserCommonTestFunctionality):
    def test_refresh_with_valid_token_success_refresh(self):
        access_token = generate_access_token(self.user)
        refresh_token = generate_refresh_token(self.user)
        # time to update access and refresh token
        time.sleep(3)
        refresh_token_data = {"refresh_token": refresh_token}
        response = self.client.post(
            reverse("api:refresh"), refresh_token_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["access_token"], access_token)
        self.assertNotEqual(response.data["refresh_token"], refresh_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access_token']}"
        )
        response = self.client.get(reverse("api:detail"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_refresh_with_expired_token_failed(self):
        self.user.refresh_token_expires_at = (
            timezone.now() - settings.REFRESH_TOKEN_LIFETIME
        )
        refresh_token_data = {"refresh_token": self.user.refresh_token}
        response = self.client.post(
            reverse("api:refresh"), refresh_token_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_invalid_token_failed_refresh(self):
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
            response = self.client.post(reverse("api:refresh"), token, format="json")
            self.assertEqual(response.status_code, expected_status)
            self.user.refresh_from_db()
            self.assertEqual(
                refresh_token_expires_at, self.user.refresh_token_expires_at
            )
