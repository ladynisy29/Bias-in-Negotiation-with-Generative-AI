from django.test import TestCase

from users_api.models import DialogueTurn, NegotiationSession, OfferHistory, UserProfile
from users_api.services.negotiation_logic import NegotiationLogicService


class FakeOpenAIService:
    def build_messages(self, conversation_history, turn_number):
        return []

    def call_openai_api(self, messages):
        class Resp:
            message = "Counter-offer: $920,000"
            reasoning = "Small concession to continue negotiation"
            offer = 920000

        return Resp()

    def extract_offer_from_message(self, message):
        return 920000


class DialogueTrackingTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username="tester",
            password_hash="hash",
            age=25,
            gender="F",
            education_level="master",
            negotiation_experience="some",
        )
        self.session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=980000,
            initial_offer=900000,
        )
        self.logic = NegotiationLogicService.__new__(NegotiationLogicService)
        self.logic.openai_service = FakeOpenAIService()

    def test_process_message_creates_human_and_ai_turns(self):
        result = self.logic.process_message(self.session, "I offer 900000", 900000)

        self.assertEqual(result["turn_count"], 1)
        self.assertEqual(DialogueTurn.objects.filter(session=self.session).count(), 2)
        self.assertEqual(OfferHistory.objects.filter(session=self.session).count(), 2)

    def test_concession_calculation(self):
        self.logic.process_message(self.session, "I offer 900000", 900000)
        offers = OfferHistory.objects.filter(session=self.session).order_by("created_at")

        self.assertIsNone(offers[0].concession_amount)
        self.assertEqual(offers[1].concession_amount, -20000)
        self.assertAlmostEqual(offers[1].concession_percentage, -2.2222222, places=4)

    def test_dialogue_history_retrieval(self):
        self.logic.process_message(self.session, "I offer 900000", 900000)
        history = self.logic.get_dialogue_history(self.session)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["speaker"], "Human")
        self.assertEqual(history[1]["speaker"], "AI")
