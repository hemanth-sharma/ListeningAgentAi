"""
app/scraper/router.py  — simplified now that Celery drives live polling.
 
POST /scraper/run is kept for:
  1. Manual on-demand scrape from the dashboard ("Fetch now" button).
  2. Triggering a backfill on project creation.
 
Recurring live polls are driven by Celery Beat (scraper_tasks.py),
NOT by this endpoint. This endpoint is synchronous-ish: it kicks off
a Celery task and returns the job ID immediately.
"""
 
import time
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.projects import service as project_service
from app.keywords import service as keyword_service
from app.keywords.models import KeywordType
from app.scraper.schemas import ScraperRunRequest, ScrapedItem, GoScrapeResult
from app.scraper import service as scraper_service
 
# Import the Celery tasks
from app.workers.scraper_tasks import poll_project_live, backfill_project
 
router = APIRouter(prefix="/scraper", tags=["Scraper"])
 
 
@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_scraper(
    payload: ScraperRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a scrape for a project.
    Returns a Celery job ID immediately; results arrive asynchronously.
 
    For live polling, don't call this — Celery Beat handles it automatically
    once a project is activated.
    """
    # 1. Verify ownership
    project = await project_service.get_project(
        db=db, project_id=payload.project_id, owner_id=current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
 
    # 2. Fetch project configuration
    active_platforms = getattr(project, "platforms", ["reddit"])
    target_subreddits = getattr(project, "target_subreddits", [])
 
    if not active_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No platforms configured for this project.",
        )
 
    # 3. Load keywords
    keywords = await keyword_service.get_keywords(db=db, project_id=payload.project_id)
    include_keywords = [kw.keyword for kw in keywords if kw.keyword_type == KeywordType.INCLUDE]
    exclude_keywords = [kw.keyword for kw in keywords if kw.keyword_type == KeywordType.EXCLUDE]
    brand_keywords   = [kw.keyword for kw in keywords if kw.keyword_type == KeywordType.BRAND]
 
    if not include_keywords and not brand_keywords:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No include or brand keywords configured for this project.",
        )
 
    project_str_id = str(payload.project_id)
 
    # 4. Dispatch the appropriate Celery task
    if payload.backfill:
        job = backfill_project.delay(
            project_id=project_str_id,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            brand_keywords=brand_keywords,
            platforms=active_platforms,
            subreddits=target_subreddits,
        )
        return {
            "status": "accepted",
            "mode": "backfill",
            "job_id": job.id,
            "message": "Backfill started. Results will be available within a few minutes.",
        }
    else:
        job = poll_project_live.delay(
            project_id=project_str_id,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            brand_keywords=brand_keywords,
            platforms=active_platforms,
            subreddits=target_subreddits,
        )
        return {
            "status": "accepted",
            "mode": "live",
            "job_id": job.id,
            "message": "Live poll started.",
        }
 
 
@router.get("/job/{job_id}", status_code=status.HTTP_200_OK)
async def get_scraper_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Check the status of a scraper job by Celery task ID.
    Frontend can poll this after triggering a manual run.
    """
    from app.workers.celery_app import celery
    from celery.result import AsyncResult
 
    result = AsyncResult(job_id, app=celery)
    response = {
        "job_id": job_id,
        "status": result.status,  # PENDING | STARTED | SUCCESS | FAILURE | RETRY
    }
    if result.successful():
        response["result"] = result.get()
    elif result.failed():
        response["error"] = str(result.result)
 
    return response