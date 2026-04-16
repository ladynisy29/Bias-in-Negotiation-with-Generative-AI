from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from users_api.auth import create_access_token
from users_api.models import DialogueTurn, NegotiationSession, UserProfile


@override_settings(
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SESSION_TRANSCRIPT_EMAIL_ENABLED=True,
    SESSION_TRANSCRIPT_EMAIL_RECIPIENTS=["research@example.com"],
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class TranscriptEmailHookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserProfile.objects.create(
            username="hook_user",
            password_hash="hash",
            age=27,
            gender="M",
            education_level="bachelor",
            negotiation_experience="some",
        )
        self.token, _ = create_access_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_submit_final_offer_sends_email(self):
        session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=1_000_000,
            initial_offer=900000,
            turn_count=5,
            session_status="in_progress",
            dropoff_stage="mid_negotiation",
        )
        for turn in range(1, 6):
            DialogueTurn.objects.create(
                session=session,
                turn_number=turn,
                speaker="Human",
                message=f"Turn {turn}",
                offer_made=True,
                offer_amount=900000 + turn,
                message_length=6,
            )

        response = self.client.post(
            reverse("submit-final-offer", kwargs={"session_id": session.session_id}),
            {"final_offer": 960000},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(session.session_id), mail.outbox[0].subject)

    def test_abandon_session_sends_email(self):
        session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=1_000_000,
            initial_offer=900000,
            turn_count=2,
            session_status="in_progress",
            dropoff_stage="mid_negotiation",
        )
        DialogueTurn.objects.create(
            session=session,
            turn_number=1,
            speaker="Human",
            message="Offer 905000",
            offer_made=True,
            offer_amount=905000,
            message_length=12,
        )

        response = self.client.post(
            reverse("session-abandon", kwargs={"session_id": session.session_id}),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(session.session_id), mail.outbox[0].subject)
