import json
import aiohttp
from config import API_URL


async def register_user(tg_id: int, name: str, invited_by: int | None):
    if invited_by is not None:
        payload = {"telegram_id": tg_id, "name": name, "invited_by": invited_by}
    else:
        payload = {"telegram_id": tg_id, "name": name}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL + "/api/users/", json=payload) as resp:
            text = await resp.text()
            print("STATUS:", resp.status, flush=True)
            print("BODY:", text, flush=True)
            return text


async def user_exists(tg_id: int) -> bool:
    url = f"{API_URL}/api/users/?telegram_id={tg_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            print("DEBUG RAW:", text, flush=True)

            if resp.status != 200:
                return False

            data = json.loads(text)
            print("DEBUG JSON:", data, flush=True)
            return len(data) > 0
