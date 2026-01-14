# myapp/domain/infrastructure/amnezia_gateway.py
import httpx


class AmneziaGateway:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip("/")

    def get_stats(self):
        try:
            url = f"{self.api_url}/api/wg/stats"
            response = httpx.get(
                url, headers={"accept": "application/json"}, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
