# myapp/domain/subscription/services.py
from datetime import date
import uuid
from myapp.tasks.provisioning import sync_vpn_cluster
from myapp.domain.infrastructure.yookassa_gateway import create_recurring_payment
from myapp.models import Payment, TelegramUser
from celery import shared_task
from myapp.domain.user_service import calculate_new_end_date
from django.db import transaction
from myapp.domain.inviter.services import apply_inviter_bonus
from myapp.domain.infrastructure.telegram_gateway import (
    send_message,
    send_message_to_admin_chanel,
)


@shared_task
def extend_subscription_task(user_id, months):
    """Добавляет месяцы к подписке пользователя и запускает синхронизацию"""
    print(
        f"extend_subscription_task user_id={user_id}, months={months}",
        flush=True,
    )

    inviter_to_notify = None
    target_user_tg_id = None

    # 1. Атомарно обновляем данные в БД
    with transaction.atomic():
        user = TelegramUser.objects.select_for_update().get(id=user_id)
        target_user_tg_id = user.telegram_id

        print(f"user found: {user.name}, current end_date: {user.end_date}", flush=True)

        # Рассчитываем и сохраняем новую дату
        user.end_date = calculate_new_end_date(user.end_date, months)

        # Логика рефералов
        inviter = apply_inviter_bonus(user)
        user.save()

        if inviter:
            inviter.save()
            inviter_to_notify = {
                "tg_id": inviter.telegram_id,
                "inviter_name": inviter.name,
                "referral_name": user.name,
            }

    # 2. Отправляем уведомления (вне транзакции)
    if inviter_to_notify:
        send_message(
            inviter_to_notify["tg_id"],
            f"Вам начислено +20 дней за приглашение {inviter_to_notify['referral_name']}!",
        )
        send_message_to_admin_chanel(
            f"Пользователю: {inviter_to_notify['inviter_name']} - {inviter_to_notify['tg_id']} "
            f"начислено +20 дней\nза приглашение {inviter_to_notify['referral_name']}!",
        )

    # 3. ЗАПУСКАЕМ СИНХРОНИЗАЦИЮ
    # Теперь, когда транзакция завершена (commit), данные в БД актуальны
    if target_user_tg_id:
        print(f"Triggering sync_vpn_cluster for {target_user_tg_id}", flush=True)
        sync_vpn_cluster.delay(target_user_tg_id)  # type: ignore


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
