from py3xui import Api
from django_api.myapp.domain.infrastructure.servers_schema import XrayServer
from typing import Any, cast


class XrayGateway:
    def __init__(self, server: XrayServer):
        self.api = Api(
            host=server.base_url,
            username=server.username,
            password=server.password,
        )

    def add_user(self, inbound_id: int, email: str, days: int):
        clients = [
            {
                "email": email,
                "enable": True,
                "expiry_time": days * 24 * 3600,
            }
        ]
        return self.api.client.add(inbound_id=inbound_id, clients=cast(Any, clients))
