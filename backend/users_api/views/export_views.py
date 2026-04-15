import csv
import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.auth import get_authenticated_user
from users_api.models import NegotiationSession
from users_api.services.negotiation_logic import NegotiationLogicService


class ExportSessionsCsvView(APIView):
    def get(self, request):
        user = get_authenticated_user(request)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "session_id",
                "user_id",
                "started_at",
                "ended_at",
                "turn_count",
                "ai_reservation_price",
                "initial_offer",
                "final_offer",
                "final_price",
                "outcome",
                "session_status",
                "dropoff_stage",
                "human_profit",
                "ai_profit",
            ]
        )

        for session in NegotiationSession.objects.filter(user=user).order_by("started_at"):
            writer.writerow(
                [
                    str(session.session_id),
                    str(session.user_id),
                    session.started_at.isoformat(),
                    session.ended_at.isoformat() if session.ended_at else "",
                    session.turn_count,
                    session.ai_reservation_price,
                    session.initial_offer,
                    session.final_offer,
                    session.final_price,
                    session.outcome,
                    session.session_status,
                    session.dropoff_stage,
                    session.human_profit,
                    session.ai_profit,
                ]
            )

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sessions_export.csv"'
        return response


class ExportTranscriptView(APIView):
    logic = NegotiationLogicService()

    def get(self, request, session_id):
        user = get_authenticated_user(request)
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        if session.user_id != user.user_id:
            return Response({"error": "Access denied."}, status=403)
        participant_profile = {
            "user_id": str(session.user.user_id),
            "age": session.user.age,
            "gender": session.user.gender,
            "location": session.user.location,
            "nationality": session.user.nationality,
            "native_language": session.user.native_language,
            "occupation": session.user.occupation,
            "education_level": session.user.education_level,
            "negotiation_experience": session.user.negotiation_experience,
            "created_at": session.user.created_at.isoformat() if session.user.created_at else None,
        }
        return Response(
            {
                "session_id": str(session.session_id),
                "participant_profile": participant_profile,
                "conversation": self.logic.get_dialogue_history(session),
                "offer_progression": self.logic.offer_progression(session),
                "concession_pattern": self.logic.calculate_concession_pattern(session),
                "session_summary": self.logic.session_summary_statistics(session),
                "session_status": session.session_status,
                "dropoff_stage": session.dropoff_stage,
            }
        )


class ExportProfitAnalysisView(APIView):
    def get(self, request):
        user = get_authenticated_user(request)
        sessions = NegotiationSession.objects.filter(user=user)
        total = sessions.count()
        accepted = sessions.filter(outcome="Accepted").count()
        declined = sessions.filter(outcome="Declined").count()

        total_human_profit = sum(s.human_profit for s in sessions)
        total_ai_profit = sum(s.ai_profit for s in sessions)

        return Response(
            {
                "total_sessions": total,
                "accepted_sessions": accepted,
                "declined_sessions": declined,
                "acceptance_rate": (accepted / total) if total else 0,
                "total_human_profit": total_human_profit,
                "total_ai_profit": total_ai_profit,
                "average_human_profit": (total_human_profit / total) if total else 0,
                "average_ai_profit": (total_ai_profit / total) if total else 0,
            }
        )
