from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users_api.models import NegotiationSession, UserProfile


class SessionManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = UserProfile.objects.create(
            username="session_user_1",
            password_hash="hash",
            age=23,
            gender="F",
            education_level="master",
            negotiation_experience="some",
        )
        self.user2 = UserProfile.objects.create(
            username="session_user_2",
            password_hash="hash",
            age=28,
            gender="M",
            education_level="bachelor",
            negotiation_experience="none",
        )

    def test_start_session_creates_session_and_random_rp(self):
        response = self.client.post(
            reverse("start-session"),
            {"user_id": str(self.user1.user_id), "initial_offer": 900000},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = NegotiationSession.objects.get(session_id=response.data["session_id"])
        self.assertGreaterEqual(session.ai_reservation_price, 850000)
        self.assertLessEqual(session.ai_reservation_price, 1150000)
        self.assertEqual(session.turn_count, 0)

    def test_start_session_rejects_second_active_session(self):
        NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.post(
            reverse("start-session"),
            {"user_id": str(self.user1.user_id), "initial_offer": 900000},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("session", response.data)

    def test_session_detail_respects_isolation(self):
        session = NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.get(
            reverse("session-detail", kwargs={"session_id": session.session_id}),
            {"user_id": str(self.user2.user_id)},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_message_respects_isolation(self):
        session = NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.post(
            reverse("send-message", kwargs={"session_id": session.session_id}),
            {"user_id": str(self.user2.user_id), "message": "Hello", "offer": 900000},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
