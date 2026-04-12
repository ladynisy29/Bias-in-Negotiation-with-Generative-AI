import json
import re
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError, RateLimitError
from rest_framework.exceptions import ValidationError


SYSTEM_PROMPT = (
    "You are the best negotiator in the world, and you are a factory seller negotiating the sale of a factory with a selling price of seller_price. "
    "You can accept a human offer only if it is between 95% and 100% of seller_price (inclusive). "
    "If the offer is outside that range, decline and propose a counter-offer with a reason but do not hit the accepted price just convince the buyer. "
    "Do not explicitly reveal your exact acceptable range, percentages, thresholds, or internal decision rules. "
    "Focus on persuasive negotiation language that explains value and invites improved offers. "
    "Before replying, always analyze the human's reason and offer, then craft a convincing response from that analysis. "
    "Stay firm but reasonable. "
    "Your JSON 'offer' must always be a positive USD number greater than 0, even when declining. "
    "You must always return strict JSON with keys: message (string), reasoning (string), offer (number)."
)


@dataclass
class AIResponse:
    message: str
    reasoning: str
    offer: float


class OpenAIService:
    def __init__(self) -> None:
        self.client = None
        self._client_init_error = None
        self._client_kwargs = None
        if settings.OPENAI_API_KEY:
            self._client_kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                self._client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL
        self.timeout_seconds = settings.OPENAI_TIMEOUT_SECONDS
        self.max_retries = settings.OPENAI_MAX_RETRIES

    def _get_client(self) -> OpenAI | None:
        if self.client is not None:
            return self.client
        if self._client_kwargs is None:
            return None
        if self._client_init_error is not None:
            return None
        try:
            self.client = OpenAI(**self._client_kwargs)
        except Exception as exc:
            self._client_init_error = exc
            return None
        return self.client

    def build_messages(
        self,
        conversation_history: list[dict[str, Any]],
        turn_number: int,
        latest_offer: float | None = None,
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "system", "content": f"Current turn: {turn_number}/5"})
        if latest_offer is not None:
            messages.append(
                {
                    "role": "system",
                    "content": f"Latest human offer for this turn is ${float(latest_offer):.2f}. Use this as the provided offer.",
                }
            )
        for item in conversation_history:
            role = "assistant" if item["speaker"] == "AI" else "user"
            content = str(item.get("message", ""))
            if role == "user" and item.get("offer_amount") is not None:
                content = f"Reason: {content}\nOffer: ${float(item['offer_amount']):.2f}"
            messages.append({"role": role, "content": content})
        return messages

    def call_openai_api(self, messages: list[dict[str, str]]) -> AIResponse:
        client = self._get_client()
        if not client:
            if self._client_init_error is not None:
                return self._fallback_response(messages, reason=f"OpenAI client init failed: {self._client_init_error}")
            return self._fallback_response(messages)

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                completion = client.chat.completions.create(
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
            except ValidationError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break

        return self._fallback_response(messages, reason=f"OpenAI unavailable: {last_error}")

    def _fallback_response(self, messages: list[dict[str, str]], reason: str | None = None) -> AIResponse:
        user_messages = [item.get("content", "") for item in messages if item.get("role") == "user"]
        latest_user_message = user_messages[-1] if user_messages else ""
        latest_offer = self.extract_offer_from_message(latest_user_message) or 900_000

        turn_number = 1
        for item in messages:
            content = str(item.get("content", ""))
            turn_match = re.search(r"Current turn:\s*(\d+)/5", content)
            if turn_match:
                turn_number = int(turn_match.group(1))
                break

        anchor_offer = 1_120_000 - ((turn_number - 1) * 30_000)
        ai_offer = max(anchor_offer, latest_offer * 1.02)
        ai_offer = max(1.0, round(ai_offer, 2))

        fallback_reason = (
            reason
            if reason
            else "Deterministic fallback mode (no OpenAI key configured)."
        )
        return AIResponse(
            message=f"I can move to ${ai_offer:,.0f} this round.",
            reasoning=fallback_reason,
            offer=ai_offer,
        )

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
