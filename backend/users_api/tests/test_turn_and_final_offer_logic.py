from django.test import TestCase
from rest_framework.exceptions import ValidationError

from users_api.models import DialogueTurn, NegotiationSession, UserProfile
from users_api.services.negotiation_logic import NegotiationLogicService


class FakeOpenAIService:
    def build_messages(self, conversation_history, turn_number):
        return []

    def call_openai_api(self, messages):
        class Resp:
            message = "Counter-offer: $920,000"
            reasoning = "Controlled concession"
            offer = 920000

        return Resp()

    def extract_offer_from_message(self, message):
        return 920000


class TurnAndFinalOfferLogicTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username="turn_logic_user",
            password_hash="hash",
            age=30,
            gender="F",
            education_level="master",
            negotiation_experience="extensive",
        )
        self.session = NegotiationSession.objects.create(
            user=self.user,
            ai_reservation_price=1_000_000,
            initial_offer=900000,
            turn_count=0,
        )
        self.logic = NegotiationLogicService.__new__(NegotiationLogicService)
        self.logic.openai_service = FakeOpenAIService()

    def _seed_turns(self, total_turns: int) -> None:
        for idx in range(1, total_turns + 1):
            DialogueTurn.objects.create(
                session=self.session,
                turn_number=idx,
                speaker="Human",
                message=f"Seed turn {idx}",
                offer_made=True,
                offer_amount=900000 + idx,
                message_length=len(f"Seed turn {idx}"),
            )

    def test_turn_counter_increments_each_exchange(self):
        self.logic.process_message(self.session, "Turn 1", 900000)
        self.session.refresh_from_db()
        self.assertEqual(self.session.turn_count, 1)

    def test_turn_rejection_after_five_turns(self):
        self.session.turn_count = 5
        self.session.save(update_fields=["turn_count"])

        with self.assertRaises(ValidationError):
            self.logic.process_message(self.session, "Extra turn", 900000)

    def test_final_offer_acceptance_logic(self):
        self.session.turn_count = 5
        self.session.save(update_fields=["turn_count"])
        self._seed_turns(5)

        result = self.logic.evaluate_final_offer(self.session, 960000)
        self.assertEqual(result["outcome"], "Accepted")
        self.assertEqual(result["final_price"], 960000)

    def test_final_offer_rejection_logic(self):
        self.session.turn_count = 5
        self.session.save(update_fields=["turn_count"])
        self._seed_turns(5)

        result = self.logic.evaluate_final_offer(self.session, 900000)
        self.assertEqual(result["outcome"], "Declined")
        self.assertIsNone(result["final_price"])

    def test_final_offer_requires_turn_five(self):
        self.session.turn_count = 4
        self.session.save(update_fields=["turn_count"])

        with self.assertRaises(ValidationError):
            self.logic.evaluate_final_offer(self.session, 960000)

    def test_process_message_turn_five_auto_finalizes(self):
        self.session.turn_count = 4
        self.session.save(update_fields=["turn_count"])
        self._seed_turns(4)

        result = self.logic.process_message(self.session, "Final round offer", 960000)
        self.session.refresh_from_db()

        self.assertEqual(result["turn_count"], 5)
        self.assertIn(result["outcome"], ["Accepted", "Declined"])
        self.assertEqual(self.session.turn_count, 5)
        self.assertEqual(self.session.outcome, result["outcome"])
