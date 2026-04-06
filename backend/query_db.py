import argparse
import csv
import sqlite3
from pathlib import Path


def connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
        """
    ).fetchall()
    print("\n== Tables ==")
    for row in rows:
        print(f"- {row['name']}")


def latest_users(conn: sqlite3.Connection, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT user_id, age, gender, location, nationality, created_at
        FROM users_api_userprofile
        ORDER BY created_at DESC
        LIMIT ?;
        """,
        (limit,),
    ).fetchall()
    print("\n== Latest Users ==")
    for row in rows:
        print(dict(row))


def latest_sessions(conn: sqlite3.Connection, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT
            session_id,
            user_id,
            turn_count,
            outcome,
            session_status,
            dropoff_stage,
            initial_offer,
            final_offer,
            final_price,
            started_at,
            ended_at
        FROM users_api_negotiationsession
        ORDER BY started_at DESC
        LIMIT ?;
        """,
        (limit,),
    ).fetchall()
    print("\n== Latest Sessions ==")
    for row in rows:
        print(dict(row))


def session_detail(conn: sqlite3.Connection, session_id: str) -> None:
    session = conn.execute(
        """
        SELECT
            session_id,
            user_id,
            turn_count,
            outcome,
            session_status,
            dropoff_stage,
            initial_offer,
            final_offer,
            final_price,
            started_at,
            ended_at,
            human_profit,
            ai_profit
        FROM users_api_negotiationsession
        WHERE session_id = ?;
        """,
        (session_id,),
    ).fetchone()
    if not session:
        print(f"\nSession not found: {session_id}")
        return

    print("\n== Session ==")
    print(dict(session))

    turns = conn.execute(
        """
        SELECT
            turn_number,
            speaker,
            message,
            offer_amount,
            concession_amount,
            offer_made,
            is_counter_offer,
            response_time_seconds,
            message_length,
            sentiment,
            strategy_tag,
            timestamp
        FROM users_api_dialogueturn
        WHERE session_id = ?
        ORDER BY turn_number, timestamp;
        """,
        (session_id,),
    ).fetchall()

    print("\n== Turns ==")
    for row in turns:
        print(dict(row))


def export_all_csv(conn: sqlite3.Connection, output_path: str) -> Path:
    target = Path(output_path)
    if not target.is_absolute():
        target = Path.cwd() / target
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

    users = conn.execute(
        """
        SELECT user_id, age, gender, location, nationality, created_at
        FROM users_api_userprofile
        ORDER BY created_at;
        """
    ).fetchall()

    sessions = conn.execute(
        """
        SELECT
            session_id,
            user_id,
            initial_offer,
            final_offer,
            final_price,
            outcome,
            session_status,
            dropoff_stage,
            started_at,
            ended_at,
            turn_count,
            (julianday(ended_at) - julianday(started_at)) * 86400.0 AS session_duration_seconds
        FROM users_api_negotiationsession
        ORDER BY started_at;
        """
    ).fetchall()

    turns = conn.execute(
        """
        SELECT
            d.session_id,
            s.user_id,
            d.turn_number,
            d.speaker,
            d.message,
            d.offer_amount,
            d.concession_amount,
            d.offer_made,
            d.is_counter_offer,
            d.response_time_seconds,
            d.message_length,
            d.sentiment,
            d.strategy_tag,
            d.timestamp
        FROM users_api_dialogueturn d
        JOIN users_api_negotiationsession s ON d.session_id = s.session_id
        ORDER BY d.timestamp;
        """
    ).fetchall()

    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()

        for row in users:
            writer.writerow(
                {
                    "row_type": "users",
                    "user_id": row["user_id"],
                    "age": row["age"],
                    "gender": row["gender"],
                    "location": row["location"],
                    "nationality": row["nationality"],
                    "created_at": row["created_at"],
                }
            )

        for row in sessions:
            writer.writerow(
                {
                    "row_type": "sessions",
                    "user_id": row["user_id"],
                    "session_id": row["session_id"],
                    "initial_offer": row["initial_offer"],
                    "final_offer": row["final_offer"],
                    "final_price": row["final_price"],
                    "outcome": row["outcome"],
                    "session_status": row["session_status"],
                    "dropoff_stage": row["dropoff_stage"],
                    "started_at": row["started_at"],
                    "ended_at": row["ended_at"],
                    "session_duration_seconds": row["session_duration_seconds"],
                    "turn_count": row["turn_count"],
                }
            )

        for row in turns:
            writer.writerow(
                {
                    "row_type": "turns",
                    "user_id": row["user_id"],
                    "session_id": row["session_id"],
                    "turn_number": row["turn_number"],
                    "speaker": row["speaker"],
                    "message": row["message"],
                    "offer_amount": row["offer_amount"],
                    "concession_amount": row["concession_amount"],
                    "offer_made": row["offer_made"],
                    "is_counter_offer": row["is_counter_offer"],
                    "response_time_seconds": row["response_time_seconds"],
                    "message_length": row["message_length"],
                    "sentiment": row["sentiment"],
                    "strategy_tag": row["strategy_tag"],
                    "timestamp": row["timestamp"],
                }
            )

    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query local SQLite negotiation data via Python.")
    parser.add_argument("--db", default="db.sqlite3", help="Path to SQLite DB file (default: db.sqlite3)")
    parser.add_argument("--tables", action="store_true", help="List tables")
    parser.add_argument("--latest-users", type=int, default=0, help="Show latest N users")
    parser.add_argument("--latest-sessions", type=int, default=0, help="Show latest N sessions")
    parser.add_argument("--session-id", default="", help="Show complete details for one session")
    parser.add_argument(
        "--export-all-csv",
        default="",
        help="Export all collected app data into one CSV file path (example: all_collected_data.csv)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    with connect_db(args.db) as conn:
        no_explicit_action = not any(
            [
                args.tables,
                args.latest_users > 0,
                args.latest_sessions > 0,
                bool(args.session_id),
                bool(args.export_all_csv),
            ]
        )

        if args.tables or no_explicit_action:
            list_tables(conn)
        if args.latest_users > 0 or no_explicit_action:
            latest_users(conn, args.latest_users if args.latest_users > 0 else 10)
        if args.latest_sessions > 0 or no_explicit_action:
            latest_sessions(conn, args.latest_sessions if args.latest_sessions > 0 else 10)
        if args.session_id:
            session_detail(conn, args.session_id)
        if args.export_all_csv:
            output = export_all_csv(conn, args.export_all_csv)
            print(f"\nCSV export created: {output}")


if __name__ == "__main__":
    main()
