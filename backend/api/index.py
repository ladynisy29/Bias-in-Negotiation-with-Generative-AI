import os
import sys
from pathlib import Path

# Ensure Django project modules are importable when running as a Vercel function.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
