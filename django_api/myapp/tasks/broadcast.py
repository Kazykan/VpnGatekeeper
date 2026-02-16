# myapp/tasks/broadcast.py
import time
import logging
from celery import shared_task
from myapp.domain.infrastructure.telegram_gateway import send_message
from myapp.models import TelegramUser

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_mass_message_task(self, user_ids, message_text):
    """
    Рассылка по списку ID с учетом лимитов Telegram.
    """
    users = TelegramUser.objects.filter(id__in=user_ids)
    total = users.count()
    success = 0
    blocked = 0

    for index, user in enumerate(users):
        # Используем ваш gateway
        result = send_message(user.telegram_id, message_text)

        if result:
            success += 1
        else:
            # Если send_message вернул None, значит была ошибка (чаще всего бот заблокирован)
            blocked += 1

        # Лимит TG: 30 сообщений в секунду.
        # Делаем паузу каждые 25 сообщений, чтобы не упереться в Flood Wait
        if (index + 1) % 25 == 0:
            time.sleep(1.2)

    return f"Рассылка завершена: {success} доставлено, {blocked} не удалось."
