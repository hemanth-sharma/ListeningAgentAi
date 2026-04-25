import httpx
import json
import os
from datetime import datetime
import uuid
from app.config import settings

async def call_scraper(payload: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(settings.GO_SCRAPER_URL, json=payload)
        res.raise_for_status()
        return res.json()


def save_raw_data(mission_id: str, data: list):
    date = datetime.utcnow().strftime("%Y-%m-%d")
    batch_id = str(uuid.uuid4())

    base_path = f"../redarky_data/raw/{mission_id}/{date}"
    os.makedirs(base_path, exist_ok=True)

    file_path = f"{base_path}/{batch_id}.json"

    with open(file_path, "w") as f:
        json.dump(data, f)

    return file_path