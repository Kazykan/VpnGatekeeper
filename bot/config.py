import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8000/miniapppage.html")
