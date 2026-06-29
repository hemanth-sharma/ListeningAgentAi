import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.projects import service as project_service
from app.sources.schemas import SubredditAddRequest, MonitoredSourceResponse
from app.sources import service as sources_service

# Mount these as project sub-resources for clear dashboard execution paths
router = APIRouter(prefix="/projects/{project_id}/sources", tags=["Sources"])

@router.post("", response_model=MonitoredSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_subreddit(
    project_id: uuid.UUID,
    payload: SubredditAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Links a subreddit to a user's project workspace.
    Triggers shared global tracking initialization routines via service logic.
    """
    # 1. Enforce multi-tenant access protection: ensure project belongs to current_user
    project = await project_service.get_project(db=db, project_id=project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project environment not found or access denied"
        )
        
    if not payload.subreddit.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Subreddit identifier cannot be empty"
        )

    # 2. Invoke shared-scraping allocation pipeline
    return await sources_service.add_subreddit_to_project(
        db=db, 
        project_id=project_id, 
        subreddit=payload.subreddit
    )


@router.delete("/{subreddit}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subreddit(
    project_id: uuid.UUID,
    subreddit: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Removes tracking metadata links from a specific project.
    Automated back-end logic spins down Apify allocations if subscriber matrix drops to zero.
    """
    # 1. Access guard check
    project = await project_service.get_project(db=db, project_id=project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project environment not found or access denied"
        )

    # 2. Safely trigger decrementation / removal
    await sources_service.remove_subreddit_from_project(
        db=db, 
        project_id=project_id, 
        subreddit=subreddit
    )
    return None