# myapp/domain/subscription/calculations.py
from dataclasses import dataclass
from datetime import date
import time


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
