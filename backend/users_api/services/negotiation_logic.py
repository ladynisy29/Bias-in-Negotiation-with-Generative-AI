from collections import defaultdict
from dataclasses import asdict, dataclass

from django.db.models import Avg, Max, Min
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users_api.models import DialogueTurn, NegotiationSession, OfferHistory
from users_api.services.openai_service import OpenAIService
from users_api.services.validators import validate_message, validate_positive_number


@dataclass
class NegotiationTurnResult:
    ai_message: str
    ai_reasoning: str
    ai_offer: float
    turn_count: int


class NegotiationLogicService:
    def __init__(self) -> None:
        self.openai_service = OpenAIService()

    def process_message(self, session: NegotiationSession, message: str, offer: float) -> dict:
        validate_message(message)
        validate_positive_number(offer, "offer")

        if session.turn_count >= 5:
            raise ValidationError({"turn_count": "Maximum turns reached."})

        turn_number = session.turn_count + 1
        self._create_dialogue_turn(session, turn_number, "Human", message, float(offer), None)
        self._create_offer_history(session, turn_number, float(offer), "Human")

        conversation_history = self._get_conversation_history(session)
        ai_response = self.openai_service.call_openai_api(
            self.openai_service.build_messages(conversation_history, turn_number)
        )

        extracted_offer = self.openai_service.extract_offer_from_message(ai_response.message)
        ai_offer = extracted_offer or ai_response.offer

        self._create_dialogue_turn(
            session,
            turn_number,
            "AI",
            ai_response.message,
            ai_offer,
            ai_response.reasoning,
        )
        self._create_offer_history(session, turn_number, ai_offer, "AI")

        session.turn_count = turn_number
        session.save(update_fields=["turn_count"])

        result = NegotiationTurnResult(
            ai_message=ai_response.message,
            ai_reasoning=ai_response.reasoning,
            ai_offer=ai_offer,
            turn_count=session.turn_count,
        )
        return asdict(result)

    def _create_dialogue_turn(
        self,
        session: NegotiationSession,
        turn_number: int,
        speaker: str,
        message: str,
        extracted_offer: float | None,
        reasoning: str | None,
    ) -> DialogueTurn:
        return DialogueTurn.objects.create(
            session=session,
            turn_number=turn_number,
            speaker=speaker,
            message=message,
            extracted_offer=extracted_offer,
            reasoning=reasoning,
        )

    def _create_offer_history(
        self,
        session: NegotiationSession,
        turn_number: int,
        offer_amount: float,
        speaker: str,
    ) -> OfferHistory:
        previous_offer = (
            OfferHistory.objects.filter(session=session).order_by("-created_at").values_list("offer_amount", flat=True).first()
        )

        concession_amount = None
        concession_percentage = None
        if previous_offer is not None and previous_offer > 0:
            concession_amount = previous_offer - offer_amount
            concession_percentage = (concession_amount / previous_offer) * 100

        return OfferHistory.objects.create(
            session=session,
            turn_number=turn_number,
            offer_amount=offer_amount,
            speaker=speaker,
            concession_amount=concession_amount,
            concession_percentage=concession_percentage,
        )

    def _get_conversation_history(self, session: NegotiationSession) -> list[dict[str, str]]:
        turns = DialogueTurn.objects.filter(session=session).order_by("turn_number", "created_at")
        return [{"speaker": t.speaker, "message": t.message} for t in turns]

    def get_dialogue_history(self, session: NegotiationSession) -> list[dict]:
        turns = DialogueTurn.objects.filter(session=session).order_by("turn_number", "created_at")
        return [
            {
                "turn_id": str(item.turn_id),
                "turn_number": item.turn_number,
                "speaker": item.speaker,
                "message": item.message,
                "extracted_offer": item.extracted_offer,
                "reasoning": item.reasoning,
                "created_at": item.created_at.isoformat(),
            }
            for item in turns
        ]

    def calculate_concession_pattern(self, session: NegotiationSession) -> dict:
        offers = OfferHistory.objects.filter(session=session).order_by("turn_number", "created_at")
        concession_values = [row.concession_amount for row in offers if row.concession_amount is not None]

        average = sum(concession_values) / len(concession_values) if concession_values else 0
        direction_counts = defaultdict(int)
        for amount in concession_values:
            if amount > 0:
                direction_counts["decrease"] += 1
            elif amount < 0:
                direction_counts["increase"] += 1
            else:
                direction_counts["flat"] += 1

        return {
            "average_concession": average,
            "concession_values": concession_values,
            "direction": dict(direction_counts),
        }

    def offer_progression(self, session: NegotiationSession) -> list[dict]:
        offers = OfferHistory.objects.filter(session=session).order_by("turn_number", "created_at")
        return [
            {
                "turn_number": item.turn_number,
                "speaker": item.speaker,
                "offer_amount": item.offer_amount,
                "concession_amount": item.concession_amount,
                "concession_percentage": item.concession_percentage,
                "created_at": item.created_at.isoformat(),
            }
            for item in offers
        ]

    def session_summary_statistics(self, session: NegotiationSession) -> dict:
        offers = OfferHistory.objects.filter(session=session)
        aggregates = offers.aggregate(
            min_offer=Min("offer_amount"),
            max_offer=Max("offer_amount"),
            avg_offer=Avg("offer_amount"),
        )

        return {
            "session_id": str(session.session_id),
            "turn_count": session.turn_count,
            "initial_offer": session.initial_offer,
            "final_offer": session.final_offer,
            "outcome": session.outcome,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_seconds": (
                (session.ended_at - session.started_at).total_seconds() if session.ended_at else None
            ),
            "min_offer": aggregates["min_offer"],
            "max_offer": aggregates["max_offer"],
            "avg_offer": aggregates["avg_offer"],
        }

    def evaluate_final_offer(self, session: NegotiationSession, final_offer: float) -> dict:
        validate_positive_number(final_offer, "final_offer")
        if session.turn_count < 5:
            raise ValidationError({"turn_count": "Cannot submit final offer before turn 5."})

        threshold = session.ai_reservation_price * 0.95
        accepted = float(final_offer) >= threshold

        session.final_offer = float(final_offer)
        session.outcome = "Accepted" if accepted else "Declined"
        session.final_price = float(final_offer) if accepted else None

        if accepted:
            session.human_profit = float(final_offer) - session.initial_offer
            session.ai_profit = float(final_offer) - session.ai_reservation_price
        else:
            session.human_profit = 0
            session.ai_profit = 0

        session.ended_at = timezone.now()
        session.save(
            update_fields=[
                "final_offer",
                "final_price",
                "outcome",
                "human_profit",
                "ai_profit",
                "ended_at",
            ]
        )

        return {
            "outcome": session.outcome,
            "final_price": session.final_price,
            "human_profit": session.human_profit,
            "ai_profit": session.ai_profit,
            "acceptance_threshold": threshold,
        }
