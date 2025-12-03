# myapp/infrastructure/servers_schema.py
from pydantic import BaseModel
from typing import Union


class AmneziaServer(BaseModel):
    name: str
    type: str
    host: str
    port: int
    username: str
    ssh_key_path: str
    docker_container: str = "amnezia-awg"
    wg_config_file: str = "/etc/wireguard/server.conf"


class XrayServer(BaseModel):
    name: str
    type: str
    base_url: str
    username: str
    password: str


Server = Union[AmneziaServer, XrayServer]
