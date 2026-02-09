from myapp.models import Credential


def get_new_credentials_for_user(telegram_id: int, limit: int = 3):
    return Credential.objects.filter(
        user__telegram_id=telegram_id,
        wg_conf_old_server=False,
        active=True,
    ).order_by("-id")[:limit]


def has_only_old_credentials(telegram_id: int) -> bool:
    return (
        Credential.objects.filter(user__telegram_id=telegram_id).exists()
        and not Credential.objects.filter(
            user__telegram_id=telegram_id,
            wg_conf_old_server=False,
        ).exists()
    )
