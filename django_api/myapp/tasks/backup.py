import subprocess
import os
import glob
import time
import logging
from datetime import datetime
from django.conf import settings
from celery import shared_task
import requests

logger = logging.getLogger(__name__)


def send_env_to_telegram():
    """Отправляет файл .env в Telegram"""
    env_path = "/app/.env"
    if not os.path.exists(env_path):
        logger.error("Файл .env не найден внутри контейнера!")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendDocument"
    caption = f"🔑 <b>Environment Config (.env)</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    try:
        with open(env_path, "rb") as f:
            files = {"document": ("config.env", f)}  # Переименуем для красоты в ТГ
            data = {
                "chat_id": settings.ADMIN_CHANNEL_ID,
                "caption": caption,
                "parse_mode": "HTML",
            }
            requests.post(url, data=data, files=files, timeout=30)
            return True
    except Exception as e:
        logger.error(f"Ошибка при отправке .env в TG: {e}")
        return False


def send_backup_to_telegram(filepath):
    """Отправляет файл бэкапа в Telegram как документ"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendDocument"
    caption = (
        f"💾 <b>Database Backup</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    try:
        with open(filepath, "rb") as f:
            files = {"document": f}
            data = {
                "chat_id": settings.ADMIN_CHANNEL_ID,
                "caption": caption,
                "parse_mode": "HTML",
            }
            response = requests.post(url, data=data, files=files, timeout=60)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Ошибка при отправке бэкапа в TG: {e}")
        return False


@shared_task(name="myapp.tasks.backup.create_db_backup")
def create_db_backup():
    """Создает дамп, отправляет в TG и чистит старые файлы"""
    backup_dir = "/app/backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.sql"
    filepath = os.path.join(backup_dir, filename)

    # Параметры БД
    db_name = os.environ.get("POSTGRES_DB")
    db_user = os.environ.get("POSTGRES_USER")
    db_host = os.environ.get("DB_HOST")
    db_pass = os.environ.get("POSTGRES_PASSWORD")

    # Команда дампа
    command = f"PGPASSWORD='{db_pass}' pg_dump -h {db_host} -U {db_user} {db_name} > {filepath}"

    try:
        # 1. Создаем дамп
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Бэкап создан локально: {filename}")

        # 2. Отправляем в Telegram
        if send_backup_to_telegram(filepath):
            logger.info("Бэкап успешно отправлен в Telegram")

        # 3. Удаляем старые локальные бэкапы (старше 7 дней)
        now = time.time()
        # Ищем все файлы .sql в папке бэкапов
        for f in glob.glob(os.path.join(backup_dir, "*.sql")):
            # Если файл создан более 7 дней назад (7 * 86400 секунд)
            if os.stat(f).st_mtime < now - 7 * 86400:
                os.remove(f)
                logger.info(f"Удален старый бэкап: {os.path.basename(f)}")

        send_env_to_telegram()

        return f"Success: {filename} and env sent to TG and cleaned up."

    except Exception as e:
        error_msg = f"Критическая ошибка бэкапа: {str(e)}"
        logger.error(error_msg)
        # Опционально: отправляем уведомление об ошибке через твой gateway
        # from myapp.domain.infrastructure.telegram_gateway import send_message_to_admin_chanel
        # send_message_to_admin_chanel(error_msg, is_error=True)
        return error_msg
