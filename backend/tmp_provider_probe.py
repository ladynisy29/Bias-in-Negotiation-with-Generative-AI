import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from users_api.services.openai_service import OpenAIService

service = OpenAIService()
print(f"client_configured={service.client is not None}")
response = service.call_openai_api([
    {"role": "system", "content": "Current turn: 1/5"},
    {"role": "user", "content": "My offer is $910,000 and I can close quickly."},
])
print(f"message={response.message}")
print(f"reasoning={response.reasoning}")
print(f"offer={response.offer}")
