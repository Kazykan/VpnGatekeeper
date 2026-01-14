from myapp.domain.user_service import calculate_new_end_date_days
from myapp.models import TelegramUser


def apply_inviter_bonus(user: TelegramUser) -> TelegramUser | None:
    if not user.invited_by or user.invited_bonus_given:
        return None

    inviter = TelegramUser.objects.filter(telegram_id=user.invited_by).first()

    if not inviter:
        return None

    inviter.end_date = calculate_new_end_date_days(inviter.end_date, 20)
    user.invited_bonus_given = True
    print(f"Inviter bonus applied: inviter={inviter.name}", flush=True)

    return inviter
