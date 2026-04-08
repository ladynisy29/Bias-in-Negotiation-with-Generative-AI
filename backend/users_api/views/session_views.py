import random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.models import NegotiationSession, UserProfile
from users_api.services.data_export import export_all_collected_data_csv
from users_api.services.negotiation_logic import NegotiationLogicService
from users_api.services.validators import validate_positive_number


class StartSessionView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        initial_offer = request.data.get("initial_offer")
        validate_positive_number(initial_offer, "initial_offer")

        user = get_object_or_404(UserProfile, user_id=user_id)

        active_session = NegotiationSession.objects.filter(
            user=user,
            outcome=None,
            ended_at=None
        ).first()
        if active_session:
            raise ValidationError({
                "session": "You already have an active session.",
                "session_id": str(active_session.session_id)
            })

        session = NegotiationSession.objects.create(
            user=user,
            ai_reservation_price=random.uniform(850_000, 1_150_000),
            initial_offer=float(initial_offer),
            turn_count=0,
            session_status="in_progress",
            dropoff_stage="before_offer",
        )
        return Response(
            {
                "session_id": str(session.session_id),
                "turn_count": session.turn_count,
                "session_status": session.session_status,
                "dropoff_stage": session.dropoff_stage,
                "started_at": session.started_at,
            },
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(APIView):
    logic = NegotiationLogicService()

    def get(self, request, session_id):
        session = get_object_or_404(NegotiationSession, session_id=session_id)

        requesting_user_id = request.query_params.get("user_id")
        if requesting_user_id and str(session.user.user_id) != requesting_user_id:
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "session_id": str(session.session_id),
                "turn_count": session.turn_count,
                "turns_remaining": max(0, 5 - session.turn_count),
                "initial_offer": session.initial_offer,
                "final_offer": session.final_offer,
                "outcome": session.outcome,
                "session_status": session.session_status,
                "dropoff_stage": session.dropoff_stage,
                "dialogue_turns": self.logic.get_dialogue_history(session),
                "offer_progression": self.logic.offer_progression(session),
            }
        )


class SubmitFinalOfferView(APIView):
    logic = NegotiationLogicService()

    def post(self, request, session_id):
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        requesting_user_id = request.data.get("user_id")
        if requesting_user_id and str(session.user.user_id) != str(requesting_user_id):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if session.ended_at is not None:
            return Response(
                {"error": "This session is already completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = self.logic.evaluate_final_offer(
            session,
            request.data.get("final_offer")
        )
        return Response(result)


class AbandonSessionView(APIView):
    def post(self, request, session_id):
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        requesting_user_id = request.data.get("user_id")
        if requesting_user_id and str(session.user.user_id) != str(requesting_user_id):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        if session.session_status == "completed":
            return Response({"error": "Completed session cannot be abandoned."}, status=status.HTTP_400_BAD_REQUEST)

        latest_human_offer = (
            session.dialogue_turns.filter(speaker="Human", offer_made=True)
            .order_by("-timestamp")
            .values_list("offer_amount", flat=True)
            .first()
        )

        session.outcome = "Abandoned"
        session.session_status = "abandoned"
        if session.turn_count <= 0:
            session.dropoff_stage = "before_offer"
        elif session.turn_count < 5:
            session.dropoff_stage = "mid_negotiation"
        else:
            session.dropoff_stage = "after_offer"

        session.final_offer = latest_human_offer if latest_human_offer is not None else session.initial_offer
        session.final_price = None
        session.ended_at = timezone.now()
        session.human_profit = 0
        session.ai_profit = 0
        session.save(
            update_fields=[
                "outcome",
                "session_status",
                "dropoff_stage",
                "final_offer",
                "final_price",
                "ended_at",
                "human_profit",
                "ai_profit",
            ]
        )

        try:
            export_all_collected_data_csv()
        except Exception:
            pass

        return Response(
            {
                "session_id": str(session.session_id),
                "session_status": session.session_status,
                "dropoff_stage": session.dropoff_stage,
                "outcome": session.outcome,
                "final_offer": session.final_offer,
                "ended_at": session.ended_at,
            }
        )