import httpx

from app.config import settings
from app.storage.local_s3 import LocalS3Storage

storage = LocalS3Storage()


async def call_scraper(payload: dict) -> list[dict]:
    async with httpx.AsyncClient() as client:
        res = await client.post(settings.GO_SCRAPER_URL, json=payload, timeout=30.0)
        res.raise_for_status()
        return res.json()


def save_raw_data(mission_id: str, data: list[dict]) -> str:
    return storage.write_json(layer="raw", mission_id=mission_id, payload=data)