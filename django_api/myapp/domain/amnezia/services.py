# myapp/domain/amnezia/services.py
from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from myapp.models import Credential, Server


def collect_amnezia_stats() -> list[dict]:
    # Получаем все серверы типа amnezia
    servers = Server.objects.filter(type="amnezia")
    results = []

    for server in servers:
        # Инициализируем шлюз с данными из БД
        gateway = AmneziaGateway(
            api_url=server.api_url,
            username=server.api_username,
            password=server.api_password,
        )

        stats = gateway.get_stats()

        results.append(
            {
                "id": server.id,
                "name": server.name,
                "status": "error" if "error" in stats else "ok",
                "data": stats,
            }
        )

    return results


def setup_vpn_for_user(tg_user, server):
    gateway = AmneziaGateway(
        api_url=server.api_url,
        username=server.admin_username,
        password=server.admin_password,
    )

    # Запрос к вашему FastAPI
    result = gateway.create_user(client_name=f"tg_{tg_user.telegram_id}")

    if result.get("status") == "ok":
        # Обновляем или создаем Credential
        credential, created = Credential.objects.update_or_create(
            user=tg_user,
            server=server,
            defaults={"wg_conf": result["client_conf"], "active": True},
        )
        return credential
    else:
        raise Exception(f"Amnezia API error: {result.get('output')}")
