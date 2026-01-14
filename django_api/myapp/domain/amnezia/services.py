from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from myapp.models import Server


def collect_amnezia_stats() -> list[dict]:
    servers = Server.objects.filter(type="amnezia")

    results = []

    for server in servers:
        gateway = AmneziaGateway(server.api_url)
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
