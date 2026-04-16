from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.auth import get_authenticated_user
from users_api.models import NegotiationSession
from users_api.services.negotiation_logic import NegotiationLogicService
from users_api.services.transcript_email import send_session_transcript_email


class SendMessageView(APIView):
    logic = NegotiationLogicService()

    def post(self, request, session_id):
        user = get_authenticated_user(request)
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        if session.user_id != user.user_id:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        result = self.logic.process_message(
            session=session,
            message=request.data.get("message", ""),
            offer=request.data.get("offer"),
        )
        if session.session_status == "completed" and session.ended_at is not None:
            send_session_transcript_email(session, trigger="auto-finalized-turn-five")
        return Response(result)


class DialogueHistoryView(APIView):
    logic = NegotiationLogicService()

    def get(self, request, session_id):
        user = get_authenticated_user(request)
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        if session.user_id != user.user_id:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "session_id": str(session.session_id),
                "dialogue": self.logic.get_dialogue_history(session),
                "offers": self.logic.offer_progression(session),
            }
        )
