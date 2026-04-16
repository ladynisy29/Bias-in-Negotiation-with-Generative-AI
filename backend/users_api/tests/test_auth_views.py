from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users_api.models import UserProfile


class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("auth-health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertIn("database", response.data)

    def test_uptime_ping_endpoint_returns_ok(self):
        response = self.client.get(reverse("uptime-ping"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["message"], "pong")

    def test_register_and_login_issue_token(self):
        register_response = self.client.post(
            reverse("auth-register"),
            {
                "username": "alice",
                "password": "strong-pass-123",
                "age": 26,
                "gender": "F",
                "education_level": "master",
                "negotiation_experience": "some",
            },
            format="json",
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", register_response.data)

        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "alice", "password": "strong-pass-123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", login_response.data)

        user = UserProfile.objects.get(username="alice")
        self.assertEqual(user.age, 26)
        self.assertTrue(user.password_hash.startswith("bcrypt_sha256$"))

    def test_logout_revokes_access_token(self):
        register_response = self.client.post(
            reverse("auth-register"),
            {
                "username": "charlie",
                "password": "strong-pass-123",
                "education_level": "master",
                "negotiation_experience": "some",
            },
            format="json",
        )
        token = register_response.data["access_token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        logout_response = self.client.post(reverse("auth-logout"), {}, format="json")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        protected_response = self.client.post(reverse("start-session"), {}, format="json")
        self.assertEqual(protected_response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(DEBUG=False, ALLOW_DEV_AUTH_ENDPOINTS=False)
    def test_dev_create_user_blocked_in_non_debug(self):
        response = self.client.post(
            reverse("auth-dev-create-user"),
            {"username": "test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_protected_endpoint_requires_token(self):
        user = UserProfile.objects.create(
            username="bob",
            password_hash="hash",
            education_level="bachelor",
            negotiation_experience="none",
        )
        _ = user
        response = self.client.post(reverse("start-session"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
