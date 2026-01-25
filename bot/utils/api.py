import aiohttp
from config import API_URL, DJANGO_BOT_USERNAME, DJANGO_BOT_PASSWORD


class DjangoAPI:
    def __init__(self):
        self.base = API_URL
        self.username = DJANGO_BOT_USERNAME
        self.password = DJANGO_BOT_PASSWORD
        self.access = None
        self.refresh = None

    async def login(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base}/api/token/",
                json={"username": self.username, "password": self.password},
            ) as resp:
                data = await resp.json()
                self.access = data["access"]
                self.refresh = data["refresh"]

    async def refresh_token(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base}/api/token/refresh/",
                json={"refresh": self.refresh},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access = data["access"]
                else:
                    await self.login()

    async def request(self, method, path, json=None):
        if not self.access:
            await self.login()

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{self.base}{path}",
                json=json,
                headers={"Authorization": f"Bearer {self.access}"},
            ) as resp:

                if resp.status == 401:
                    await self.refresh_token()
                    return await self.request(method, path, json)

                return await resp.json()

    # -----------------------------
    # USERS
    # -----------------------------
    async def register_user(self, tg_id: int, name: str, invited_by: int | None):
        payload = {"telegram_id": tg_id, "name": name}
        if invited_by is not None:
            payload["invited_by"] = invited_by

        return await self.request("POST", "/api/users/", json=payload)

    async def user_exists(self, tg_id: int) -> bool:
        data = await self.request("GET", f"/api/users/?telegram_id={tg_id}")
        return len(data) > 0

    # -----------------------------
    # PAYMENTS
    # -----------------------------
    async def create_payment(
        self, tg_id: int, amount: int, pay_type: str, months: int, unique_payload: str
    ):
        return await self.request(
            "POST",
            "/api/payments/create/",
            json={
                "telegram_id": tg_id,
                "amount": amount,
                "type": pay_type,  # "once" или "subscription"
                "months": months,
                "unique_payload": unique_payload,
            },
        )
