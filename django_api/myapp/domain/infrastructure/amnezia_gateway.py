import re
import paramiko
from django_api.myapp.domain.infrastructure.servers_schema import AmneziaServer


class AmneziaGateway:
    def __init__(self, server: AmneziaServer):
        self.server = server

    def add_user(self, user_id: str) -> str:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.server.host,
            port=self.server.port,
            username=self.server.username,
            key_filename=self.server.ssh_key_path,
        )
        command = f"wg add {user_id}"  # пример команды
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode().strip()
        ssh.close()
        return result

def run_ssh_command(ssh, command: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode().strip()


def create_user(CLIENT_NAME: str, ENDPOINT: str, WG_CONFIG_FILE: str,
                DOCKER_CONTAINER: str, SSH_HOST: str, TELEGRAM_ID: str) -> str:
    """
    Создает нового клиента WireGuard и возвращает ТОЛЬКО текст конфигурационного файла.
    """

    if not re.match(r'^[a-zA-Z0-9_-]+$', CLIENT_NAME):
        raise ValueError("Invalid CLIENT_NAME. Only letters, numbers, underscores, and hyphens are allowed.")

    # Подключение по SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username="root")  # ⚡️ Укажи свои креды

    # Генерация ключей
    key = run_ssh_command(ssh, f"docker exec -i {DOCKER_CONTAINER} wg genkey")
    psk = run_ssh_command(ssh, f"docker exec -i {DOCKER_CONTAINER} wg genpsk")

    # Получаем server.conf
    server_conf = run_ssh_command(ssh, f"docker exec -i {DOCKER_CONTAINER} cat {WG_CONFIG_FILE}")

    # Парсим server.conf
    server_private_key = re.search(r"^PrivateKey\s*=\s*(\S+)", server_conf, re.M).group(1)
    server_public_key = run_ssh_command(ssh, f"echo {server_private_key} | docker exec -i {DOCKER_CONTAINER} wg pubkey")
    listen_port = re.search(r"ListenPort\s*=\s*(\d+)", server_conf).group(1)
    additional_params = "\n".join(re.findall(r"^(Jc|Jmin|Jmax|S1|S2|H[1-4])\s*=\s*.*", server_conf, re.M))

    # Выбираем свободный IP
    octet = 2
    while re.search(fr"AllowedIPs\s*=\s*10\.8\.1\.{octet}/32", server_conf):
        octet += 1
    if octet > 254:
        raise RuntimeError("WireGuard internal subnet 10.8.1.0/24 is full")

    client_ip = f"10.8.1.{octet}/32"
    client_public_key = run_ssh_command(ssh, f"echo {key} | docker exec -i {DOCKER_CONTAINER} wg pubkey")

    # Добавляем клиента в server.conf (с комментарием telegram_id)
    updated_server_conf = server_conf + f"""
[Peer]
# {TELEGRAM_ID}
PublicKey = {client_public_key}
PresharedKey = {psk}
AllowedIPs = {client_ip}

"""

    # Обновляем clientsTable (метаданные)
    try:
        clients_table = run_ssh_command(ssh, f"docker exec -i {DOCKER_CONTAINER} cat /opt/amnezia/awg/clientsTable")
    except:
        clients_table = "[]"

    clients = json.loads(clients_table)
    clients.append({
        "clientId": client_public_key,
        "userData": {
            "clientName": CLIENT_NAME,
            "creationDate": datetime.now().isoformat(),
            "telegramId": TELEGRAM_ID
        }
    })
    new_clients_table = json.dumps(clients, indent=4)

    # Копируем обновленные данные обратно в контейнер
    run_ssh_command(ssh, f"echo '{updated_server_conf}' | docker exec -i {DOCKER_CONTAINER} tee {WG_CONFIG_FILE}")
    run_ssh_command(ssh, f"echo '{new_clients_table}' | docker exec -i {DOCKER_CONTAINER} tee /opt/amnezia/awg/clientsTable")
    run_ssh_command(ssh, f"docker exec -i {DOCKER_CONTAINER} sh -c 'wg-quick down {WG_CONFIG_FILE} && wg-quick up {WG_CONFIG_FILE}'")

    ssh.close()

    # Возвращаем ТОЛЬКО текст клиентского конфигурационного файла
    client_conf_text = f"""[Interface]
Address = {client_ip}
DNS = 1.1.1.1, 1.0.0.1
PrivateKey = {key}
{additional_params}
[Peer]
PublicKey = {server_public_key}
PresharedKey = {psk}
AllowedIPs = 0.0.0.0/0
Endpoint = {ENDPOINT}:{listen_port}
PersistentKeepalive = 25
"""
    return client_conf_text