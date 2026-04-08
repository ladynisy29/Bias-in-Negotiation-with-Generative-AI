import csv
from pathlib import Path

from django.conf import settings

from users_api.models import DialogueTurn, NegotiationSession, UserProfile


def export_all_collected_data_csv(output_path: str | None = None) -> Path:
    base_dir = Path(settings.BASE_DIR)
    target = Path(output_path) if output_path else (base_dir / "all_collected_data.csv")
    if not target.is_absolute():
        target = base_dir / target
    target.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "row_type",
        "user_id",
        "age",
        "gender",
        "location",
        "nationality",
        "created_at",
        "session_id",
        "initial_offer",
        "final_offer",
        "final_price",
        "outcome",
        "session_status",
        "dropoff_stage",
        "started_at",
        "ended_at",
        "session_duration_seconds",
        "turn_count",
        "turn_number",
        "speaker",
        "message",
        "offer_amount",
        "concession_amount",
        "offer_made",
        "is_counter_offer",
        "response_time_seconds",
        "message_length",
        "sentiment",
        "strategy_tag",
        "timestamp",
    ]

    users = UserProfile.objects.all().order_by("created_at")
    sessions = NegotiationSession.objects.all().order_by("started_at")
    turns = DialogueTurn.objects.all().order_by("timestamp")

    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()

        for user in users:
            writer.writerow(
                {
                    "row_type": "users",
                    "user_id": str(user.user_id),
                    "age": user.age,
                    "gender": user.gender,
                    "location": user.location,
                    "nationality": user.nationality,
                    "created_at": user.created_at.isoformat(),
                }
            )

        for session in sessions:
            duration_seconds = None
            if session.started_at and session.ended_at:
                duration_seconds = (session.ended_at - session.started_at).total_seconds()

            writer.writerow(
                {
                    "row_type": "sessions",
                    "user_id": str(session.user_id),
                    "session_id": str(session.session_id),
                    "initial_offer": session.initial_offer,
                    "final_offer": session.final_offer,
                    "final_price": session.final_price,
                    "outcome": session.outcome,
                    "session_status": session.session_status,
                    "dropoff_stage": session.dropoff_stage,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                    "session_duration_seconds": duration_seconds,
                    "turn_count": session.turn_count,
                }
            )

        for turn in turns:
            writer.writerow(
                {
                    "row_type": "turns",
                    "user_id": str(turn.session.user_id),
                    "session_id": str(turn.session_id),
                    "turn_number": turn.turn_number,
                    "speaker": turn.speaker,
                    "message": turn.message,
                    "offer_amount": turn.offer_amount,
                    "concession_amount": turn.concession_amount,
                    "offer_made": turn.offer_made,
                    "is_counter_offer": turn.is_counter_offer,
                    "response_time_seconds": turn.response_time_seconds,
                    "message_length": turn.message_length,
                    "sentiment": turn.sentiment,
                    "strategy_tag": turn.strategy_tag,
                    "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
                }
            )

    return target
