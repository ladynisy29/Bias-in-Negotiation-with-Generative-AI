import json
import logging

from django.conf import settings
from django.core.mail import EmailMessage

from users_api.models import NegotiationSession
from users_api.services.negotiation_logic import NegotiationLogicService


logger = logging.getLogger(__name__)


def build_session_transcript_payload(
    session: NegotiationSession,
    logic: NegotiationLogicService | None = None,
) -> dict:
    logic_service = logic or NegotiationLogicService()
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

    return {
        "session_id": str(session.session_id),
        "participant_profile": participant_profile,
        "conversation": logic_service.get_dialogue_history(session),
        "offer_progression": logic_service.offer_progression(session),
        "concession_pattern": logic_service.calculate_concession_pattern(session),
        "session_summary": logic_service.session_summary_statistics(session),
        "session_status": session.session_status,
        "dropoff_stage": session.dropoff_stage,
    }


def _get_recipients() -> list[str]:
    configured = getattr(settings, "SESSION_TRANSCRIPT_EMAIL_RECIPIENTS", [])
    if isinstance(configured, str):
        configured = [configured]

    recipients: list[str] = []
    for value in configured:
        recipients.extend(str(value).split(","))
    return [email.strip() for email in recipients if email and email.strip()]


def send_session_transcript_email(session: NegotiationSession, trigger: str) -> bool:
    if not getattr(settings, "SESSION_TRANSCRIPT_EMAIL_ENABLED", False):
        return False

    recipients = _get_recipients()
    if not recipients:
        logger.warning(
            "Transcript email skipped due to missing recipients",
            extra={"session_id": str(session.session_id), "trigger": trigger},
        )
        return False

    payload = build_session_transcript_payload(session)
    subject_prefix = getattr(settings, "SESSION_TRANSCRIPT_EMAIL_SUBJECT_PREFIX", "Bias")
    subject = f"{subject_prefix} transcript - session {session.session_id}"
    body = (
        "Session transcript attached.\n\n"
        f"session_id: {session.session_id}\n"
        f"user_id: {session.user.user_id}\n"
        f"outcome: {session.outcome or ''}\n"
        f"status: {session.session_status}\n"
        f"trigger: {trigger}\n"
    )

    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@bias.local"),
        to=recipients,
    )
    filename = f"session-{session.session_id}-transcript.json"
    message.attach(filename, json.dumps(payload, indent=2), "application/json")

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send transcript email",
            extra={"session_id": str(session.session_id), "trigger": trigger},
        )
        return False

    logger.info(
        "Transcript email sent",
        extra={"session_id": str(session.session_id), "trigger": trigger, "recipients": recipients},
    )
    return True
