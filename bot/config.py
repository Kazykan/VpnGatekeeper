import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8000/miniapppage.html")
DJANGO_BOT_USERNAME = os.getenv("DJANGO_SUPERUSER_USERNAME", "")
DJANGO_BOT_PASSWORD = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
