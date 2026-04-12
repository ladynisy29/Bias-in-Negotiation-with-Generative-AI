from collections import defaultdict
from dataclasses import asdict, dataclass
import logging
from typing import Literal

from django.db import transaction
from django.db.models import Avg, Max, Min
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users_api.models import DialogueTurn, NegotiationSession, OfferHistory
from users_api.services.data_export import export_all_collected_data_csv
from users_api.services.openai_service import OpenAIService
from users_api.services.validators import validate_message, validate_positive_number


logger = logging.getLogger(__name__)


@dataclass
class NegotiationTurnResult:
    ai_message: str
    ai_reasoning: str
    ai_offer: float
    turn_count: int
    outcome: str | None = None
    final_price: float | None = None
    human_profit: float | None = None
    ai_profit: float | None = None
    acceptance_threshold: float | None = None


class NegotiationLogicService:
    def __init__(self) -> None:
        self.openai_service = OpenAIService()

    def process_message(self, session: NegotiationSession, message: str, offer: float) -> dict:
        validate_message(message)
        validate_positive_number(offer, "offer")

        if session.turn_count >= 5:
            raise ValidationError({"turn_count": "Maximum turns reached."})

        turn_number = session.turn_count + 1
        initial_offer_captured = session.turn_count == 0 and (session.initial_offer or 0) <= 0
        with transaction.atomic():
            if initial_offer_captured:
                session.initial_offer = float(offer)

            self._create_dialogue_turn(
                session=session,
                turn_number=turn_number,
                speaker="Human",
                message=message,
                extracted_offer=float(offer),
                reasoning=None,
                offer_amount=float(offer),
                is_counter_offer=turn_number > 1,
            )
            self._create_offer_history(session, turn_number, float(offer), "Human")

            conversation_history = self._get_conversation_history(session)
            ai_response = self.openai_service.call_openai_api(
                self.openai_service.build_messages(
                    conversation_history,
                    turn_number,
                    latest_offer=float(offer),
                )
            )

            extracted_offer = self.openai_service.extract_offer_from_message(ai_response.message)
            ai_offer = float(ai_response.offer) if ai_response.offer is not None else extracted_offer

            self._create_dialogue_turn(
                session,
                turn_number,
                "AI",
                ai_response.message,
                ai_offer,
                ai_response.reasoning,
                offer_amount=ai_offer,
                is_counter_offer=True,
            )
            self._create_offer_history(session, turn_number, ai_offer, "AI")

            session.turn_count = turn_number
            response_outcome = None
            response_final_price = None
            response_human_profit = None
            response_ai_profit = None
            response_acceptance_threshold = None

            if turn_number == 5:
                final_result = self.evaluate_final_offer(session, float(offer))
                response_outcome = final_result["outcome"]
                response_final_price = final_result["final_price"]
                response_human_profit = final_result["human_profit"]
                response_ai_profit = final_result["ai_profit"]
                response_acceptance_threshold = final_result["acceptance_threshold"]
            else:
                update_fields = ["turn_count"]
                if initial_offer_captured:
                    update_fields.append("initial_offer")
                session.save(update_fields=update_fields)

        result = NegotiationTurnResult(
            ai_message=ai_response.message,
            ai_reasoning=ai_response.reasoning,
            ai_offer=ai_offer,
            turn_count=session.turn_count,
            outcome=response_outcome,
            final_price=response_final_price,
            human_profit=response_human_profit,
            ai_profit=response_ai_profit,
            acceptance_threshold=response_acceptance_threshold,
        )
        logger.info(
            "Negotiation turn processed",
            extra={"session_id": str(session.session_id), "turn_number": turn_number},
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
        offer_amount: float | None = None,
        is_counter_offer: bool = False,
    ) -> DialogueTurn:
        previous_offer = (
            DialogueTurn.objects.filter(session=session, offer_made=True)
            .order_by("-timestamp")
            .values_list("offer_amount", flat=True)
            .first()
        )

        concession_amount = None
        if previous_offer is not None and offer_amount is not None:
            concession_amount = previous_offer - offer_amount

        previous_turn_of_other_speaker = (
            DialogueTurn.objects.filter(session=session)
            .exclude(speaker=speaker)
            .order_by("-timestamp")
            .first()
        )
        response_time_seconds = None
        if previous_turn_of_other_speaker:
            response_time_seconds = max(
                0.0,
                (timezone.now() - previous_turn_of_other_speaker.timestamp).total_seconds(),
            )

        return DialogueTurn.objects.create(
            session=session,
            turn_number=turn_number,
            speaker=speaker,
            message=message,
            offer_made=offer_amount is not None,
            is_counter_offer=is_counter_offer,
            offer_amount=offer_amount,
            concession_amount=concession_amount,
            response_time_seconds=response_time_seconds,
            message_length=len(message),
            sentiment=self._infer_sentiment(message),
            strategy_tag=self._infer_strategy(message),
            extracted_offer=extracted_offer,
            reasoning=reasoning,
        )

    def _infer_sentiment(self, message: str) -> Literal["positive", "neutral", "negative"]:
        text = message.lower()
        positive_words = ("agree", "great", "deal", "good", "thanks")
        negative_words = ("no", "can't", "cannot", "refuse", "impossible")
        if any(token in text for token in positive_words):
            return "positive"
        if any(token in text for token in negative_words):
            return "negative"
        return "neutral"

    def _infer_strategy(self, message: str) -> Literal["aggressive", "cooperative", "neutral"]:
        text = message.lower()
        if any(token in text for token in ("final", "must", "non-negotiable", "take it")):
            return "aggressive"
        if any(token in text for token in ("flexible", "let's", "can we", "happy")):
            return "cooperative"
        return "neutral"

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

    def _get_conversation_history(self, session: NegotiationSession) -> list[dict]:
        turns = DialogueTurn.objects.filter(session=session).order_by("turn_number", "created_at")
        return [
            {
                "speaker": t.speaker,
                "message": t.message,
                "offer_amount": t.offer_amount,
            }
            for t in turns
        ]

    def get_dialogue_history(self, session: NegotiationSession) -> list[dict]:
        turns = DialogueTurn.objects.filter(session=session).order_by("turn_number", "created_at")
        return [
            {
                "turn_id": str(item.turn_id),
                "turn_number": item.turn_number,
                "speaker": item.speaker,
                "message": item.message,
                "offer_made": item.offer_made,
                "is_counter_offer": item.is_counter_offer,
                "offer_amount": item.offer_amount,
                "concession_amount": item.concession_amount,
                "response_time_seconds": item.response_time_seconds,
                "message_length": item.message_length,
                "sentiment": item.sentiment,
                "strategy_tag": item.strategy_tag,
                "extracted_offer": item.extracted_offer,
                "reasoning": item.reasoning,
                "timestamp": item.timestamp.isoformat(),
                "created_at": item.created_at.isoformat(),
            }
            for item in turns
        ]

    def calculate_concession_pattern(self, session: NegotiationSession) -> dict:
        turns = DialogueTurn.objects.filter(session=session, offer_made=True).order_by("turn_number", "created_at")
        concession_values = [row.concession_amount for row in turns if row.concession_amount is not None]

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
        offers = DialogueTurn.objects.filter(session=session, offer_made=True).order_by("turn_number", "created_at")
        return [
            {
                "turn_number": item.turn_number,
                "speaker": item.speaker,
                "offer_amount": item.offer_amount,
                "concession_amount": item.concession_amount,
                "concession_percentage": (
                    ((item.concession_amount / (item.offer_amount + item.concession_amount)) * 100)
                    if item.concession_amount is not None
                    and item.offer_amount is not None
                    and (item.offer_amount + item.concession_amount) not in (0, None)
                    else None
                ),
                "is_counter_offer": item.is_counter_offer,
                "timestamp": item.timestamp.isoformat(),
                "created_at": item.created_at.isoformat(),
            }
            for item in offers
        ]

    def session_summary_statistics(self, session: NegotiationSession) -> dict:
        offers = DialogueTurn.objects.filter(session=session, offer_made=True)
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

        min_acceptable_offer = float(session.ai_reservation_price) * 0.95
        accepted = float(final_offer) >= min_acceptable_offer

        # Ensure terminal turn state is persisted when finalizing from the 5th chat turn.
        session.turn_count = max(session.turn_count, 5)

        session.final_offer = float(final_offer)
        session.outcome = "Accepted" if accepted else "Declined"
        session.session_status = "completed"
        session.dropoff_stage = "after_offer"
        session.final_price = float(final_offer) if accepted else None

        if accepted:
            session.human_profit = float(final_offer) - float(session.initial_offer)
            session.ai_profit = float(final_offer) - float(session.ai_reservation_price)
        else:
            session.human_profit = 0
            session.ai_profit = 0

        session.ended_at = timezone.now()
        session.save(
            update_fields=[
                "turn_count",
                "final_offer",
                "final_price",
                "outcome",
                "session_status",
                "dropoff_stage",
                "human_profit",
                "ai_profit",
                "ended_at",
            ]
        )

        self.validate_session_integrity(session)

        # Keep a continuously fresh one-file export without manual command execution.
        try:
            export_all_collected_data_csv()
        except Exception:
            pass

        return {
            "outcome": session.outcome,
            "final_price": session.final_price,
            "human_profit": session.human_profit,
            "ai_profit": session.ai_profit,
            "acceptance_threshold": min_acceptable_offer,
        }

    def validate_session_integrity(self, session: NegotiationSession) -> None:
        missing = {}
        if session.outcome is None:
            missing["session_outcome"] = "Missing required outcome."
        if session.final_offer is None:
            missing["session_final_offer"] = "Missing required final_offer."
        if session.ended_at is None:
            missing["session_ended_at"] = "Missing required ended_at timestamp."

        for turn in range(1, session.turn_count + 1):
            if not DialogueTurn.objects.filter(session=session, turn_number=turn).exists():
                missing[f"turn_{turn}"] = "Missing at least one message for this turn."

        if missing:
            raise ValidationError({"session_integrity": missing})
