from fastapi import APIRouter
from app.scraper.schemas import ScrapeRequest, ScrapedItem
from app.scraper.service import call_scraper, save_raw_data
from app.workers.tasks import process_batch

router = APIRouter()


@router.post("/run/{mission_id}")
async def run_scraper(mission_id: str, payload: ScrapeRequest):
    # 1. Call Go scraper
    data = await call_scraper(payload.model_dump())
    validated_data = [ScrapedItem.model_validate(item).model_dump(mode="json") for item in data]

    # 2. Save raw data (s3)
    file_path = save_raw_data(mission_id, validated_data)

    # 3. Trigger Celery task
    process_batch.delay(mission_id, file_path)

    return {
        "status": "success",
        "items_fetched": len(validated_data),
        "file_path": file_path,
    }