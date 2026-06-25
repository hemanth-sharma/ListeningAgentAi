import httpx
from typing import List
from app.config import settings
from app.storage.local_s3 import LocalS3Storage

storage = LocalS3Storage()

async def call_scraper(payload: dict) -> List[dict]:
    async with httpx.AsyncClient() as client:
        # Hits Go microservice (at http://localhost:8080/scrape)
        res = await client.post(f"{settings.GO_SCRAPER_URL}/scrape", json=payload, timeout=45.0)
        res.raise_for_status()
        return res.json()

def save_raw_project_data(project_id: str, data: List[dict]) -> str:
    # using LocalS3Storage layout, organized cleanly by project_id
    return storage.write_json(layer="raw", mission_id=project_id, payload=data)