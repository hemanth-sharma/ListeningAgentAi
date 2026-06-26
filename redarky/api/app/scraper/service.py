import httpx
from typing import List
from app.config import settings
from app.storage.local_s3 import LocalS3Storage
import logging


storage = LocalS3Storage()

logger = logging.getLogger("uvicorn.error")

async def call_scraper(payload: dict) -> List[dict]:
    async with httpx.AsyncClient() as client:
        url = settings.GO_SCRAPER_URL
        if not url.endswith("/scrape"):
            url = f"{url}/scrape"

        try:
            logger.info(f"Sending payload to Go Scraper: {payload}")
            res = await client.post(url, json=payload, timeout=45.0)
            
            # If Go returns a bad status code (e.g. 400, 500), this raises an exception
            res.raise_for_status() 
            
            data = res.json()
            if data is None:
                logger.warning(f"Go scraper returned an empty response body or literal null for URL: {url}")
                return []
                
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Go scraper HTTP Error {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Failed to communicate with Go scraper service: {str(e)}")
            return []

def save_raw_project_data(project_id: str, data: List[dict]) -> str:
    # using LocalS3Storage layout, organized cleanly by project_id
    return storage.write_json(layer="raw", mission_id=project_id, payload=data)