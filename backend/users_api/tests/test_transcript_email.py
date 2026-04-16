import json

from django.core import mail
from django.test import TestCase, override_settings

from users_api.models import DialogueTurn, NegotiationSession, UserProfile
from users_api.services.transcript_email import build_session_transcript_payload, send_session_transcript_email


class TranscriptEmailServiceTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username="mail_user",
            password_hash="hash",
            age=29,
            gender="F",
            location="Berlin",
            nationality="German",
            native_language="German",
            occupation="Analyst",
            education_level="master",
            negotiation_experience="some",
        )
        self.session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=950000,
            initial_offer=900000,
            final_offer=955000,
            final_price=955000,
            outcome="Accepted",
            session_status="completed",
            dropoff_stage="after_offer",
            turn_count=1,
            human_profit=55000,
            ai_profit=5000,
        )
        DialogueTurn.objects.create(
            session=self.session,
            turn_number=1,
            speaker="Human",
            message="I can do 955000.",
            offer_made=True,
            offer_amount=955000,
            message_length=16,
        )

    def test_build_session_transcript_payload_includes_participant_profile(self):
        payload = build_session_transcript_payload(self.session)
        self.assertEqual(payload["participant_profile"]["native_language"], "German")
        self.assertEqual(payload["participant_profile"]["occupation"], "Analyst")
        self.assertEqual(payload["session_id"], str(self.session.session_id))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SESSION_TRANSCRIPT_EMAIL_ENABLED=True,
        SESSION_TRANSCRIPT_EMAIL_RECIPIENTS=["research@example.com"],
        DEFAULT_FROM_EMAIL="no-reply@example.com",
    )
    def test_send_session_transcript_email_sends_json_attachment(self):
        sent = send_session_transcript_email(self.session, trigger="test")

        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(self.session.session_id), mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["research@example.com"])
        self.assertEqual(len(mail.outbox[0].attachments), 1)

        filename, content, mime_type = mail.outbox[0].attachments[0]
        self.assertTrue(filename.endswith("-transcript.json"))
        self.assertEqual(mime_type, "application/json")

        parsed = json.loads(content)
        self.assertIn("participant_profile", parsed)
        self.assertEqual(parsed["session_summary"]["session_id"], str(self.session.session_id))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SESSION_TRANSCRIPT_EMAIL_ENABLED=False,
        SESSION_TRANSCRIPT_EMAIL_RECIPIENTS=["research@example.com"],
    )
    def test_send_session_transcript_email_skips_when_disabled(self):
        sent = send_session_transcript_email(self.session, trigger="test-disabled")
        self.assertFalse(sent)
        self.assertEqual(len(mail.outbox), 0)
