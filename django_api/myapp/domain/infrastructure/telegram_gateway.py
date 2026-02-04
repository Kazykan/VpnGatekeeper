from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
ADMIN_CHANNEL_ID = settings.ADMIN_CHANNEL_ID


def send_message(chat_id, text, parse_mode="HTML"):
    """Базовая функция с защитой от превышения лимита"""
    url = f"{TELEGRAM_API_URL}/sendMessage"

    # Обрезаем текст до последних 3800 символов, если он слишком длинный
    if len(text) > 3800:
        text = "...[обрезано]...\n" + text[-3800:]

    payload = {"chat_id": str(chat_id), "text": text, "parse_mode": parse_mode}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Если ошибка в самом канале, пишем в локальный лог сервера
        print(f"!!! TG ERROR: {e}", flush=True)
        logger.error(f"Не удалось отправить лог в Telegram канал: {e}")
        return None


def send_message_to_admin_chanel(text, is_error=False):
    """
    Отправка логов и статусов в админ-канал.
    is_error=True обернет текст в блок кода для удобства.
    """
    if not ADMIN_CHANNEL_ID:
        return None

    if is_error:
        # Оформляем как блок кода для удобства чтения стектрейсов
        formatted_text = f"❌ <b>ERROR LOG:</b>\n<pre>{text}</pre>"
    else:
        formatted_text = f"ℹ️ <b>STATUS:</b>\n{text}"

    return send_message(ADMIN_CHANNEL_ID, formatted_text)
