from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from users_api.services.openai_service import OpenAIService


class OpenAIServiceParsingTests(SimpleTestCase):
    def setUp(self):
        self.service = OpenAIService.__new__(OpenAIService)

    def test_parse_ai_response_valid(self):
        payload = self.service.parse_ai_response(
            '{"message": "I can do $950,000", "reasoning": "Conceding slightly", "offer": 950000}'
        )
        self.assertEqual(payload["offer"], 950000)

    def test_parse_ai_response_missing_key(self):
        with self.assertRaises(ValidationError):
            self.service.parse_ai_response('{"message": "x", "offer": 1}')

    def test_extract_offer_currency(self):
        offer = self.service.extract_offer_from_message("I can accept $950,000 today.")
        self.assertEqual(offer, 950000)

    def test_extract_offer_k_format(self):
        offer = self.service.extract_offer_from_message("Let us settle at 950k.")
        self.assertEqual(offer, 950000)

    def test_extract_offer_million_format(self):
        offer = self.service.extract_offer_from_message("My final ask is 1.2 million.")
        self.assertEqual(offer, 1200000)

    def test_extract_offer_not_found(self):
        offer = self.service.extract_offer_from_message("I need to think about it.")
        self.assertIsNone(offer)

    def test_call_openai_api_uses_fallback_when_client_missing(self):
        service = OpenAIService.__new__(OpenAIService)
        service.client = None
        service.model = "gpt-4.1-mini"
        service.timeout_seconds = 5
        service.max_retries = 1

        result = service.call_openai_api(
            [
                {"role": "system", "content": "Current turn: 2/5"},
                {"role": "user", "content": "My offer is $900,000"},
            ]
        )

        self.assertIn("$", result.message)
        self.assertGreater(result.offer, 0)
