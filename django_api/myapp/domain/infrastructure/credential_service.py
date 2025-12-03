import json
from pathlib import Path
from typing import List
from django_api.myapp.domain.infrastructure.servers_schema import AmneziaServer, XrayServer, Server
from django_api.myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from django_api.myapp.domain.infrastructure.xray_gateway import XrayGateway


def load_servers() -> List[Server]:
    path = Path(__file__).resolve().parent.parent / "infrastructure" / "servers.json"
    with open(path) as f:
        raw = json.load(f)

    servers: List[Server] = []
    for s in raw:
        if s["type"] == "amnezia":
            servers.append(AmneziaServer(**s))
        elif s["type"] == "xray":
            servers.append(XrayServer(**s))
    return servers


def add_user_to_all_servers(user_id: str, email: str, days: int):
    servers = load_servers()
    results = {}

    for server in servers:
        if isinstance(server, AmneziaServer):
            gateway = AmneziaGateway(server)
            results[server.name] = gateway.add_user(user_id)

        elif isinstance(server, XrayServer):
            gateway = XrayGateway(server)
            inbound_id = getattr(server, "inbound_id", 1)  # можно добавить в JSON
            results[server.name] = gateway.add_user(inbound_id, email, days)

    return results
