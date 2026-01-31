from datetime import date
import uuid
from myapp.domain.infrastructure.yookassa_gateway import create_recurring_payment
from myapp.models import Payment, TelegramUser
from celery import shared_task
from myapp.domain.user_service import calculate_new_end_date
from django.db import transaction
from myapp.domain.inviter.services import apply_inviter_bonus
from myapp.domain.infrastructure.telegram_gateway import send_message


@shared_task
def extend_subscription_task(user_id, months):
    """Добавляет месяцы к подписке пользователя"""
    print(
        f"extend_subscription_task user_id={user_id}, months={months}",
        flush=True,
    )
    with transaction.atomic():
        user = TelegramUser.objects.select_for_update().get(id=user_id)

        print(f"user found: {user.name}, current end_date: {user.end_date}", flush=True)
        user.end_date = calculate_new_end_date(user.end_date, months)
        inviter = apply_inviter_bonus(user)

        user.save()

        if inviter:
            inviter.save()
            send_message(
                inviter.telegram_id,
                f"Вам начислено +20 дней за приглашение {user.name}!",
            )


def process_autopayment_for_user(user_id):
    """
    Создает новый платеж на основе предыдущего и инициирует списание в ЮKassa
    """
    try:
        user = TelegramUser.objects.get(id=user_id)
    except TelegramUser.DoesNotExist:
        print(f"Критическая ошибка: Пользователь с ID {user_id} не найден в БД.")
        return

    try:
        # Находим последний успешный платеж, чтобы понять тариф (сумма и срок)
        last_payment = (
            Payment.objects.filter(user=user, status="success")
            .order_by("-payment_time")
            .first()
        )

        if not last_payment:
            print(f"User {user_id} has no successful payments for reference.")
            return

        # 1. Создаем новую запись платежа в БД со статусом pending
        new_payment = Payment.objects.create(
            user=user,
            amount=last_payment.amount,
            months=last_payment.months,
            status="pending",
            unique_payload=f"auto_{uuid.uuid4().hex[:10]}",  # Уникальный ключ для базы
        )

        # 2. Формируем метаданные для ЮKassa
        metadata = {"payment_id": new_payment.id, "is_auto_charge": True}

        # 3. Делаем запрос в ЮKassa (тихое списание)
        yk_res = create_recurring_payment(
            amount_rub=new_payment.amount,
            payment_method_id=user.payment_method_id,
            description=f"Автопродление подписки ({new_payment.months} мес.)",
            metadata=metadata,
        )

        # Если ЮKassa сразу вернула успех (так часто бывает при рекуррентных)
        if yk_res.status == "succeeded":
            # Мы не вызываем продление тут, так как оно придет через Webhook
            # Но если вы хотите супер-надежности, можно вызвать и здесь.
            # Безопаснее дождаться вебхука, как и при обычной оплате.
            pass

    except Exception as e:
        print(f"Autopayment failed for user {user_id}: {e}")
        send_message(
            user.telegram_id,
            "⚠️ Не удалось выполнить автосписание. Проверьте баланс карты.",
        )
