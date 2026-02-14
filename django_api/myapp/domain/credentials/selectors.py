from myapp.models import Credential, TelegramUser
from django.db.models import Sum


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


def get_user_traffic_report(user: TelegramUser) -> dict:
    """
    Формирует детальный отчет по трафику для всех подключений пользователя.
    """
    credentials = Credential.objects.filter(user=user).select_related("server")

    # Агрегируем общие данные (с учетом смещения за месяц)
    total_raw = credentials.aggregate(total=Sum("total_traff"))["total"] or 0
    total_offset = credentials.aggregate(offset=Sum("traffic_offset"))["offset"] or 0

    # Реальный расход за месяц по всем серверам
    monthly_total_bytes = total_raw - total_offset
    if monthly_total_bytes < 0:
        monthly_total_bytes = 0

    details = []
    for cred in credentials:
        # Расчет для конкретного подключения
        usage = cred.total_traff - cred.traffic_offset
        if usage < 0:
            usage = 0

        details.append(
            {
                "credential_id": cred.id,
                "server_name": cred.server.name,
                "server_type": cred.server.type,
                "monthly_usage_gb": round(usage / (1024**3), 3),
                "total_lifetime_gb": cred.total_gb,
                "last_seen": cred.last_seen.isoformat() if cred.last_seen else None,
                "is_active": cred.active,
            }
        )

    return {
        "user_id": user.telegram_id,
        "user_name": user.name,
        "summary": {
            "monthly_total_gb": round(monthly_total_bytes / (1024**3), 3),
            "total_lifetime_gb": round(total_raw / (1024**3), 3),
            "active_connections": credentials.filter(active=True).count(),
        },
        "details": details,
    }


def get_active_credentials_for_user(user):
    return Credential.objects.filter(user=user, active=True).select_related("server")
