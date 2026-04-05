import json
import re
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError, RateLimitError
from rest_framework.exceptions import APIException, ValidationError


SYSTEM_PROMPT = (
    "You are a factory seller negotiating price. Stay firm but reasonable. "
    "You must always return strict JSON with keys: message (string), "
    "reasoning (string), offer (number)."
)


@dataclass
class AIResponse:
    message: str
    reasoning: str
    offer: float


class OpenAIService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL
        self.timeout_seconds = settings.OPENAI_TIMEOUT_SECONDS
        self.max_retries = settings.OPENAI_MAX_RETRIES

    def build_messages(self, conversation_history: list[dict[str, Any]], turn_number: int) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "system", "content": f"Current turn: {turn_number}/5"})
        for item in conversation_history:
            role = "assistant" if item["speaker"] == "AI" else "user"
            messages.append({"role": role, "content": item["message"]})
        return messages

    def call_openai_api(self, messages: list[dict[str, str]]) -> AIResponse:
        if not self.client:
            raise APIException("OPENAI_API_KEY is missing.")

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    timeout=self.timeout_seconds,
                )
                raw = completion.choices[0].message.content or ""
                parsed = self.parse_ai_response(raw)
                return AIResponse(
                    message=parsed["message"],
                    reasoning=parsed["reasoning"],
                    offer=float(parsed["offer"]),
                )
            except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
                last_error = exc
                backoff = 2 ** attempt
                time.sleep(backoff)
            except ValidationError:
                raise
            except Exception as exc:
                last_error = exc
                break

        raise APIException(f"AI service temporarily unavailable: {last_error}")

    def parse_ai_response(self, raw_response: str) -> dict[str, Any]:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValidationError({"ai_response": f"Malformed JSON from AI: {exc}"})

        required_keys = {"message", "reasoning", "offer"}
        if not required_keys.issubset(payload):
            raise ValidationError({"ai_response": "AI JSON missing required keys: message, reasoning, offer."})

        if not isinstance(payload["message"], str) or not payload["message"].strip():
            raise ValidationError({"ai_response": "message must be a non-empty string."})
        if not isinstance(payload["reasoning"], str) or not payload["reasoning"].strip():
            raise ValidationError({"ai_response": "reasoning must be a non-empty string."})

        try:
            offer = float(payload["offer"])
        except (TypeError, ValueError):
            raise ValidationError({"ai_response": "offer must be numeric."})
        if offer <= 0:
            raise ValidationError({"ai_response": "offer must be > 0."})

        payload["offer"] = offer
        return payload

    def extract_offer_from_message(self, message: str) -> float | None:
        patterns = [
            r"\$([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?)",
            r"\b([0-9]+(?:\.[0-9]+)?)\s*(k|thousand)\b",
            r"\b([0-9]+(?:\.[0-9]+)?)\s*(m|million)\b",
            r"\b([0-9]{5,})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if not match:
                continue

            number = float(match.group(1).replace(",", ""))
            if len(match.groups()) >= 2:
                unit = (match.group(2) or "").lower()
                if unit in {"k", "thousand"}:
                    number *= 1_000
                elif unit in {"m", "million"}:
                    number *= 1_000_000

            if number > 0:
                return number

        return None
