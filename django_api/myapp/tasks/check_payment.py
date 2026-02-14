from celery import shared_task
from myapp.domain.infrastructure.yookassa_gateway import get_payment_info
from myapp.models import Payment
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_payment_status(self, internal_payment_id: int):
    try:
        # 1. Достаем платеж из нашей БД
        local_payment = Payment.objects.get(id=internal_payment_id)

        if local_payment.status == "success":
            logger.info(f"Платеж {internal_payment_id} уже подтвержден.")
            return

        # ПРОВЕРКА ДЛЯ PYLANCE: если ID провайдера нет, дальше идти нельзя
        if not local_payment.provider_payment_id:
            logger.error(
                f"У платежа {internal_payment_id} отсутствует provider_payment_id"
            )
            return

        # 2. Спрашиваем ЮKassa (теперь Pylance уверен, что тут str)
        yk_payment = get_payment_info(local_payment.provider_payment_id)

        if yk_payment.status == "succeeded":
            local_payment.status = "success"
            local_payment.save()
            logger.info(f"Платеж {internal_payment_id} подтвержден через ЮKassa")

        elif yk_payment.status in ["pending", "waiting_for_capture"]:
            # Перезапуск через 10 минут
            raise self.retry(countdown=600)

        elif yk_payment.status == "canceled":
            local_payment.status = "failed"
            local_payment.save()
            logger.warning(f"Платеж {internal_payment_id} отменен пользователем")

    except Payment.DoesNotExist:
        logger.error(f"Платеж {internal_payment_id} не найден в базе")
    except Exception as exc:
        # Если это self.retry, пробрасываем его дальше
        if isinstance(exc, self.retry_backoff):
            raise exc
        logger.error(f"Ошибка в Celery задаче: {exc}")
        raise self.retry(exc=exc, countdown=60)
