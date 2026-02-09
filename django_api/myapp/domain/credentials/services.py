from datetime import date
from myapp.models import TelegramUser, Credential, Server
from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from myapp.tasks.provisioning import sync_vpn_cluster


def generate_new_config_for_user(user: TelegramUser) -> None:
    """
    Бизнес-сценарий:
    - проверить подписку
    - заблокировать старые конфиги
    - создать новый конфиг
    """

    # 1️⃣ Проверка подписки
    if not user.end_date or user.end_date < date.today():
        raise NoActiveSubscription

    # 2️⃣ Блокировка старых конфигов
    old_server = Server.objects.filter(
        type="amnezia", name__icontains="Old_server"
    ).first()

    old_credentials = Credential.objects.filter(
        user=user,
        wg_conf_old_server=True,
        active=True,
    )

    if old_server and old_credentials.exists():
        gateway = AmneziaGateway(
            api_url=old_server.api_url,
            username=old_server.api_username,
            password=old_server.api_password,
        )

        for cred in old_credentials:
            if cred.wg_conf_ip:
                gateway.block_ip(cred.wg_conf_ip)
            cred.active = False
            cred.save(update_fields=["active"])

    # 3️⃣ Создание нового конфига (через cluster sync)
    sync_vpn_cluster.delay(user.telegram_id)  # type: ignore
