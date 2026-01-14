from datetime import date
from myapp.models import TelegramUser
from myapp.domain.user_service import calculate_new_end_date
from django.db import transaction
from myapp.domain.inviter.services import apply_inviter_bonus
from myapp.domain.infrastructure.telegram_gateway import send_message


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
