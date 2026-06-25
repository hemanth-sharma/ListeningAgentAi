import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user 
from app.auth.models import User
from app.posts.schemas import PostCreate, PostUpdate, PostResponse
from app.posts import service
from app.projects import service as project_service

router = APIRouter(tags=["Posts"])

@router.get("/posts", response_model=List[PostResponse])
async def read_posts(
    project_id: Optional[uuid.UUID] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if project_id:
        project = await project_service.get_project(db=db, project_id=project_id, owner_id=current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return await service.get_posts(db=db, project_id=project_id, source=source, search=search)

@router.get("/posts/{id}", response_model=PostResponse)
async def read_post(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await service.get_post(db=db, post_id=id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/projects/{project_id}/posts", response_model=List[PostResponse])
async def read_project_posts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await project_service.get_project(db=db, project_id=project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return await service.get_posts(db=db, project_id=project_id)

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = await project_service.get_project(db=db, project_id=post_in.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return await service.create_post(db=db, post_in=post_in)