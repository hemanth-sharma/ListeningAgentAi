import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user  # Import your auth logic
from app.auth.models import User
from app.posts.schemas import PostCreate, PostUpdate, PostResponse
from app.posts import service

router = APIRouter(tags=["Posts"])

# GET /posts (with query filters)
@router.get("/posts", response_model=List[PostResponse])
async def read_posts(
    project_id: Optional[uuid.UUID] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.get_posts(db=db, project_id=project_id, platform=platform, search=search)

# GET /posts/{id}
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

# GET /projects/{project_id}/posts
@router.get("/projects/{project_id}/posts", response_model=List[PostResponse])
async def read_project_posts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.get_posts(db=db, project_id=project_id)

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post_in: PostCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await service.create_post(db=db, post_in=post_in)