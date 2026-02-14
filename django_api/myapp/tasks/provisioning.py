# myapp/tasks/provisioning.py
import logging
from django.utils import timezone
from celery import shared_task
from myapp.models import TelegramUser

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_vpn_cluster(self, telegram_id):
    try:
        from myapp.domain.credentials.services import sync_xray_user_credentials

        user = TelegramUser.objects.get(telegram_id=telegram_id)
        sync_xray_user_credentials(user)

    except TelegramUser.DoesNotExist:
        logger.error(f"User {telegram_id} not found")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="myapp.tasks.mass_sync_credentials")
def mass_sync_xray_credentials():
    """
    Обновляет ключи для всех активных пользователей,
    у которых не истёк срок действия (end_date > today).
    """
    from myapp.domain.credentials.services import sync_xray_user_credentials

    today = timezone.now().date()
    # Фильтруем пользователей: есть xray_id и подписка еще активна
    active_users = TelegramUser.objects.filter(
        end_date__gte=today, xray_id__isnull=False
    )

    total = active_users.count()
    logger.info(f"🚀 Запуск массовой синхронизации для {total} пользователей...")

    for user in active_users:
        try:
            # Вызываем вашу существующую бизнес-логику
            sync_xray_user_credentials(user)
        except Exception as e:
            logger.error(
                f"❌ Ошибка синхронизации пользователя {user.telegram_id}: {e}"
            )

    logger.info("✅ Массовая синхронизация завершена.")
