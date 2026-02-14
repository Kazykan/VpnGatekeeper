# core/log_handlers.py
import logging
import requests
from django.conf import settings


class TelegramHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            # Лимит Telegram 4096 символов, оставим запас
            if len(log_entry) > 4000:
                log_entry = log_entry[:3900] + "\n... [Текст обрезан]"

            payload = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": f"🚨 **CRITICAL ERROR**\n```\n{log_entry}\n```",
                "parse_mode": "Markdown",
            }

            requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage",
                json=payload,
                timeout=10,
            )
        except Exception:
            pass  # Если упал сам логгер, приложение не должно встать
