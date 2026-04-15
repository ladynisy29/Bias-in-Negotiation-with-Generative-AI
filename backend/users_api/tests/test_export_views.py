from django.test import TestCase
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from users_api.auth import create_access_token
from users_api.models import NegotiationSession, UserProfile


@override_settings(SECURE_SSL_REDIRECT=False)
class ExportViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserProfile.objects.create(
            username="exporter",
            password_hash="hash",
            age=31,
            gender="M",
            location="Paris",
            nationality="French",
            native_language="French",
            occupation="Engineer",
            education_level="bachelor",
            negotiation_experience="extensive",
        )
        self.session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=950000,
            initial_offer=900000,
            final_offer=910000,
            final_price=910000,
            outcome="Accepted",
            human_profit=10000,
            ai_profit=-40000,
            turn_count=5,
        )
        self.token, _ = create_access_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_export_sessions_csv(self):
        response = self.client.get(reverse("export-sessions"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("session_id", response.content.decode("utf-8"))

    def test_export_transcript(self):
        response = self.client.get(reverse("export-transcript", kwargs={"session_id": self.session.session_id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn("participant_profile", response.data)
        self.assertEqual(response.data["participant_profile"]["native_language"], "French")
        self.assertEqual(response.data["participant_profile"]["occupation"], "Engineer")
        self.assertIn("session_summary", response.data)

    def test_export_profit_analysis(self):
        response = self.client.get(reverse("export-profit-analysis"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_sessions"], 1)
