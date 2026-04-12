import json
import time
import urllib.error
import urllib.request

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from users_api.models import DialogueTurn, NegotiationSession  # noqa: E402


def http_json(method, url, payload=None, token=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def main():
    suffix = int(time.time())
    username = f"smoke_user_{suffix}"

    register_status, register = http_json(
        "POST",
        "http://127.0.0.1:8000/api/auth/register",
        {
            "username": username,
            "password": "smoke-pass-123",
            "age": 27,
            "gender": "X",
            "education_level": "master",
            "negotiation_experience": "some",
        },
    )
    assert register_status == 201, f"register failed: {register_status} {register}"
    access_token = register["access_token"]

    status, start = http_json(
        "POST",
        "http://127.0.0.1:8000/api/start-session",
        {},
        token=access_token,
    )
    assert status == 201, f"start-session failed: {status} {start}"

    session_id = start["session_id"]

    detail_status, detail = http_json(
        "GET",
        f"http://127.0.0.1:8000/api/session/{session_id}",
        token=access_token,
    )
    assert detail_status == 200, f"session-detail failed: {detail_status} {detail}"

    session = NegotiationSession.objects.get(session_id=session_id)
    session.turn_count = 5
    session.save(update_fields=["turn_count"])

    for turn_number in range(1, 6):
        DialogueTurn.objects.get_or_create(
            session=session,
            turn_number=turn_number,
            speaker="Human",
            defaults={
                "message": f"Smoke turn {turn_number}",
                "message_length": len(f"Smoke turn {turn_number}"),
                "offer_made": True,
                "offer_amount": float(900000 + turn_number),
            },
        )

    final_status, final = http_json(
        "POST",
        f"http://127.0.0.1:8000/api/session/{session_id}/submit-final-offer",
        {"final_offer": 960000},
        token=access_token,
    )
    assert final_status == 200, f"submit-final-offer failed: {final_status} {final}"

    print("SMOKE_OK")
    print(json.dumps({
        "session_id": session_id,
        "start": start,
        "detail_turn_count": detail.get("turn_count"),
        "final": final,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTPError {exc.code}: {body}")
