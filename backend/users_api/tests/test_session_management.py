from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users_api.auth import create_access_token
from users_api.models import DialogueTurn, NegotiationSession, UserProfile


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
        self.user1_token, _ = create_access_token(self.user1)
        self.user2_token, _ = create_access_token(self.user2)

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_start_session_creates_session_and_random_rp(self):
        self._auth(self.user1_token)
        response = self.client.post(
            reverse("start-session"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = NegotiationSession.objects.get(session_id=response.data["session_id"])
        self.assertGreaterEqual(session.ai_reservation_price, 850000)
        self.assertLessEqual(session.ai_reservation_price, 1150000)
        self.assertEqual(session.turn_count, 0)
        self.assertIn("ai_greeting", response.data)

        greeting_turn = DialogueTurn.objects.filter(session=session, turn_number=0, speaker="AI").first()
        self.assertIsNotNone(greeting_turn)
        self.assertEqual(greeting_turn.message, response.data["ai_greeting"])

    def test_start_session_rejects_second_active_session(self):
        self._auth(self.user1_token)
        NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.post(
            reverse("start-session"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("session", response.data)

    def test_session_detail_respects_isolation(self):
        self._auth(self.user2_token)
        session = NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.get(
            reverse("session-detail", kwargs={"session_id": session.session_id}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_message_respects_isolation(self):
        self._auth(self.user2_token)
        session = NegotiationSession.objects.create(
            user=self.user1,
            ai_reservation_price=900000,
            initial_offer=880000,
            turn_count=0,
        )

        response = self.client.post(
            reverse("send-message", kwargs={"session_id": session.session_id}),
            {"message": "Hello", "offer": 900000},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
