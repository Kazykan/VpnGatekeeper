from myapp.domain.infrastructure.telegram_gateway import send_message_to_admin_chanel
from myapp.domain.user_service import calculate_new_end_date_days
from myapp.models import Payment, TelegramUser


def apply_inviter_bonus(user: TelegramUser) -> TelegramUser | None:
    # 1. Базовые проверки: есть ли инвайтер и не давали ли бонус ранее
    if not user.invited_by or user.invited_bonus_given:
        return None

    # 2. Ищем инвайтера с блокировкой строки (чтобы избежать race condition при начислении)
    inviter = (
        TelegramUser.objects.select_for_update()
        .filter(telegram_id=user.invited_by)
        .first()
    )

    if not inviter:
        return None

    # 3. ПРОВЕРКА: Платил ли инвайтер сам хоть раз?
    # Проверяем наличие хотя бы одного платежа со статусом 'success'
    has_paid = Payment.objects.filter(user=inviter, status="success").exists()

    if not has_paid:
        send_message_to_admin_chanel(
            f"Bonus rejected: Inviter {inviter.telegram_id} never paid themselves."
        )
        return None

    # 4. Начисляем бонус
    inviter.end_date = calculate_new_end_date_days(inviter.end_date, 10)
    user.invited_bonus_given = True

    return inviter
