from celery import shared_task
from yookassa import Payment as YoPayment
from myapp.models import Payment
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_payment_status(self, internal_payment_id):
    try:
        # 1. Достаем платеж из нашей БД по внутреннему ID
        local_payment = Payment.objects.get(id=internal_payment_id)

        # Если он уже оплачен (через вебхук), ничего не делаем
        if local_payment.status == "success":
            logger.info(f"Платеж {internal_payment_id} уже был подтвержден вебхуком.")
            return

        # 2. Спрашиваем ЮKassa по их ID
        yk_payment = YoPayment.find_one(local_payment.provider_payment_id)

        if yk_payment.status == "succeeded":
            local_payment.status = (
                "success"  # В модели у тебя "success", а не "succeeded"
            )
            local_payment.save()
            # ТУТ ЖЕ: Логика начисления подписки пользователю!
            logger.info(f"Платеж {internal_payment_id} подтвержден через Celery")

        elif (
            yk_payment.status == "pending" or yk_payment.status == "waiting_for_capture"
        ):
            # Если всё еще ждем, можно перезапустить задачу еще через 10 минут
            # Но только если это не 3-я попытка (max_retries)
            raise self.retry(countdown=600)

        elif yk_payment.status == "canceled":
            local_payment.status = "failed"
            local_payment.save()

    except Payment.DoesNotExist:
        logger.error(f"Платеж {internal_payment_id} не найден в локальной базе")
    except Exception as exc:
        logger.error(f"Ошибка в Celery задаче: {exc}")
        raise self.retry(exc=exc, countdown=60)
