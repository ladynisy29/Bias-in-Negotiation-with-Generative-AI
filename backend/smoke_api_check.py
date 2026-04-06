import json
import time
import urllib.error
import urllib.parse
import urllib.request

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from users_api.models import NegotiationSession, UserProfile  # noqa: E402


def http_json(method, url, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def main():
    suffix = int(time.time())
    user = UserProfile.objects.create(
        username=f"smoke_user_{suffix}",
        password_hash="hash",
        age=27,
        gender="X",
        education_level="master",
        negotiation_experience="some",
    )

    status, start = http_json(
        "POST",
        "http://127.0.0.1:8000/api/start-session",
        {"user_id": str(user.user_id), "initial_offer": 900000},
    )
    assert status == 201, f"start-session failed: {status} {start}"

    session_id = start["session_id"]

    detail_status, detail = http_json(
        "GET",
        f"http://127.0.0.1:8000/api/session/{session_id}?user_id={urllib.parse.quote(str(user.user_id))}",
    )
    assert detail_status == 200, f"session-detail failed: {detail_status} {detail}"

    session = NegotiationSession.objects.get(session_id=session_id)
    session.turn_count = 5
    session.save(update_fields=["turn_count"])

    final_status, final = http_json(
        "POST",
        f"http://127.0.0.1:8000/api/session/{session_id}/submit-final-offer",
        {"user_id": str(user.user_id), "final_offer": 960000},
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
