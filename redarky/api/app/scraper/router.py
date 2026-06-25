import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User

from app.projects import service as project_service
from app.keywords import service as keyword_service
from app.keywords.models import KeywordType
from app.scraper.schemas import ScraperRunRequest, ScrapedItem
from app.scraper import service as scraper_service
from app.workers.tasks import process_batch

router = APIRouter(prefix="/scraper", tags=["Scraper"])

@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_scraper(
    payload: ScraperRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify project ownership and fetch platform target metadata
    project = await project_service.get_project(db=db, project_id=payload.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Fallback to defaults if these fields are missing on your project model
    active_platforms = getattr(project, "platforms", ["reddit"]) 
    target_subreddits = getattr(project, "target_subreddits", [])

    if not active_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No target platforms (e.g. reddit, hn) selected for this project."
        )

    # 2. Extract include keywords linked to this project
    keywords = await keyword_service.get_keywords(db=db, project_id=payload.project_id)
    include_queries = [kw.keyword for kw in keywords if kw.keyword_type == KeywordType.INCLUDE]

    if not include_queries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No 'include' keywords configured for this project."
        )

    # 3. Handle Time Bounds (default to 30-day backfill floor lookback)
    if payload.since_timestamp:
        since_time = payload.since_timestamp
    else:
        # 30 Days back in seconds = 30 * 24 * 60 * 60
        since_time = int(time.time()) - 2592000 

    # 4. Request targeted data collection via Go microservice for each search term
    all_scraped_items = []
    for query in include_queries:
        try:
            go_payload = {
                "query": query,
                "platforms": active_platforms,
                "subreddits": target_subreddits,
                "since": since_time
            }
            raw_data = await scraper_service.call_scraper(go_payload)
            all_scraped_items.extend(raw_data)
        except Exception as e:
            # Continue iterating over remaining queries if single request times out
            continue

    if not all_scraped_items:
        return {
            "status": "success",
            "message": "Scraper executed successfully but returned 0 new items within the time boundary.",
            "items_fetched": 0
        }

    # 5. Enforce structural safety boundaries via Pydantic matching
    validated_data = [
        ScrapedItem.model_validate(item).model_dump(mode="json") 
        for item in all_scraped_items
    ]

    # 6. Flush structural array down to local S3
    project_str_id = str(payload.project_id)
    file_path = scraper_service.save_raw_project_data(project_id=project_str_id, data=validated_data)

    # 7. Offload database ingestion and deduplication engine to background Celery workers
    async_job = process_batch.delay(project_str_id, file_path)

    return {
        "status": "success",
        "job_id": async_job.id,
        "items_fetched": len(validated_data),
        "file_path": file_path,
    }