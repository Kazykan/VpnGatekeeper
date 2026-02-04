import httpx
import logging

logger = logging.getLogger(__name__)


class AmneziaGateway:
    def __init__(self, api_url, username=None, password=None):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None

    def authenticate(self):
        """Получает JWT токен и сохраняет его"""
        url = f"{self.api_url}/api/auth/login"
        payload = {"username": self.username, "password": self.password}

        with httpx.Client() as client:
            response = client.post(
                url, json=payload, headers={"accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            return self.token

    def _auth_headers(self):
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _request(self, method, endpoint, data=None, params=None, timeout=10.0):
        """
        Универсальный метод для запросов с автоматической обработкой
        авторизации и обновлением токена при 401 ошибке.
        """
        if not self.token:
            self.authenticate()

        url = f"{self.api_url}{endpoint}"

        def perform_call():
            with httpx.Client() as client:
                if method.upper() == "GET":
                    return client.get(
                        url,
                        headers=self._auth_headers(),
                        params=params,
                        timeout=timeout,
                    )
                return client.post(
                    url, headers=self._auth_headers(), json=data, timeout=timeout
                )

        response = perform_call()

        # Если токен протух — обновляем и пробуем еще раз
        if response.status_code == 401:
            self.authenticate()
            response = perform_call()

        response.raise_for_status()
        return response.json()

    def get_stats(self):
        """Получить статистику сервера"""
        try:
            return self._request("GET", "/api/wg/stats")
        except Exception as e:
            return {"error": str(e)}

    def create_user(self, client_name):
        """Создать нового клиента на WireGuard"""
        payload = {"client_name": client_name}
        return self._request("POST", "/api/wg/add_client", data=payload, timeout=15.0)

    def get_configs(self):
        """Получить актуальные конфиги (wg0.conf и таблицу клиентов)"""
        try:
            return self._request("GET", "/api/wg/configs")
        except Exception as e:
            return {"error": str(e)}

    def replace_configs(self, wg_conf: str, clients_table: str):
        """Принудительно заменить файлы конфигурации на сервере"""
        payload = {
            "wg_conf": wg_conf,
            "clients_table": clients_table,
        }
        try:
            return self._request("POST", "/api/wg/replace_configs", data=payload)
        except Exception as e:
            return {"error": str(e)}

    # --- Методы управления Firewall (iptables) ---

    def unblock_ip(self, ip: str):
        """Разблокировать IP на уровне Linux firewall"""
        payload = {"ip": ip}
        return self._request("POST", "/api/wg/unblock_ip", data=payload)

    def block_ip(self, ip: str):
        """Заблокировать IP на уровне Linux firewall"""
        payload = {"ip": ip}
        return self._request("POST", "/api/wg/block_ip", data=payload)
