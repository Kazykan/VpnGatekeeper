# tasks/stats.py
import logging
from celery import shared_task
from myapp.domain.credentials.services import sync_server_traffic
from myapp.models import Server


logger = logging.getLogger(__name__)


@shared_task(name="myapp.tasks.stats.update_all_servers_traffic")
def update_all_servers_traffic():
    """Фоновая задача для обновления трафика по всем серверам"""
    servers = Server.objects.filter(type="xray", is_active=True)
    for server in servers:
        try:
            sync_server_traffic(server)
            logger.info(f"Статистика сервера {server.name} успешно обновлена")
        except Exception as e:
            logger.error(
                f"Критическая ошибка при обновлении сервера {server.name}: {e}"
            )
