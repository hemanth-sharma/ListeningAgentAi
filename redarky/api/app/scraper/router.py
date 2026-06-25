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
    # 1. Verify project ownership
    project = await project_service.get_project(db=db, project_id=payload.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # 2. Extract include keywords linked to this project
    keywords = await keyword_service.get_keywords(db=db, project_id=payload.project_id)
    include_queries = [kw.keyword for kw in keywords if kw.keyword_type == KeywordType.INCLUDE]

    if not include_queries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No 'include' keywords configured for this project."
        )

    # 3. Request data collection via Go microservice for each search term
    # Combines results into a single payload array
    all_scraped_items = []
    for query in include_queries:
        try:
            # Modify target subreddits array if you parse target sources dynamically
            go_payload = {"query": query, "subreddits": []}
            raw_data = await scraper_service.call_scraper(go_payload)
            all_scraped_items.extend(raw_data)
        except Exception as e:
            # Keep looping if one specific term causes a connectivity issue
            continue

    # 4. Enforce structural safety boundaries via Pydantic matching
    validated_data = [
        ScrapedItem.model_validate(item).model_dump(mode="json") 
        for item in all_scraped_items
    ]

    # 5. Flush structural array down to local S3
    project_str_id = str(payload.project_id)
    file_path = scraper_service.save_raw_project_data(project_id=project_str_id, data=validated_data)

    # 6. Offload database ingestion and deduplication engine to background Celery workers
    # Passing the context metadata cleanly down the stack
    async_job = process_batch.delay(project_str_id, file_path)

    return {
        "status": "success",
        "job_id": async_job.id,
        "items_fetched": len(validated_data),
        "file_path": file_path,
    }



# @router.post("/run/{mission_id}")
# async def run_scraper(mission_id: str, payload: ScrapeRequest):
#     # 1. Call Go scraper
#     data = await call_scraper(payload.model_dump())
#     validated_data = [ScrapedItem.model_validate(item).model_dump(mode="json") for item in data]

#     # 2. Save raw data (s3)
#     file_path = save_raw_data(mission_id, validated_data)

#     # 3. Trigger Celery task
#     process_batch.delay(mission_id, file_path)

#     return {
#         "status": "success",
#         "items_fetched": len(validated_data),
#         "file_path": file_path,
#     }