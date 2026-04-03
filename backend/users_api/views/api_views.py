from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.models import NegotiationSession
from users_api.services.negotiation_logic import NegotiationLogicService


class SendMessageView(APIView):
    logic = NegotiationLogicService()

    def post(self, request, session_id):
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        result = self.logic.process_message(
            session=session,
            message=request.data.get("message", ""),
            offer=request.data.get("offer"),
        )
        return Response(result)


class DialogueHistoryView(APIView):
    logic = NegotiationLogicService()

    def get(self, request, session_id):
        session = get_object_or_404(NegotiationSession, session_id=session_id)
        return Response(
            {
                "session_id": str(session.session_id),
                "dialogue": self.logic.get_dialogue_history(session),
                "offers": self.logic.offer_progression(session),
            }
        )
