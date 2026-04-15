# myapp/domain/subscription/calculations.py
import base64
from dataclasses import dataclass
from datetime import date
import time

from myapp.models import TelegramUser


@dataclass
class SubscriptionDTO:
    links: list[str]
    upload_bytes: int
    download_bytes: int
    total_limit_bytes: int
    expire_timestamp: int


# Жесткий лимит: 3 ТБ
LIMIT_3TB_BYTES = 3 * (1024**4)


def prepare_subscription_data(user, credentials) -> SubscriptionDTO:
    """Бизнес-логика подготовки данных для клиента VPN."""
    total_up = sum(c.up_traff for c in credentials)
    total_down = sum(c.down_traff for c in credentials)

    # Конвертируем дату окончания в Unix Timestamp
    expire_ts = 0
    if user.end_date:
        expire_ts = int(time.mktime(user.end_date.timetuple()))

    vless_links = [c.vless_url for c in credentials if c.vless_url]

    return SubscriptionDTO(
        links=vless_links,
        upload_bytes=total_up,
        download_bytes=total_down,
        total_limit_bytes=LIMIT_3TB_BYTES,
        expire_timestamp=expire_ts,
    )

def get_subscription_announce(user: TelegramUser):
    today = date.today()

    days_left = 0
    if user.end_date:
        days_left = (user.end_date - today).days
    
    message = ""
    
    # 1. Если подписка истекла (или сегодня последний день)
    if days_left <= 0:
        message = "❌ Подписка окончена. Нажмите на значок планеты выше для продления."
    
    # 2. Если осталось 3 дня или меньше
    elif 1 <= days_left <= 3:
        day_word = "дня" if days_left > 1 else "день"
        message = f"⚠️ Внимание! До конца подписки: {days_left} {day_word}. Продлите в боте."

    if not message:
        return None

    # Кодируем в Base64 для корректной передачи спецсимволов и кириллицы
    encoded = base64.b64encode(message.encode('utf-8')).decode('utf-8')
    return f"base64:{encoded}"