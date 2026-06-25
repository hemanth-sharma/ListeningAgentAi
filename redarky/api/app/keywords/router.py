import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.keywords.schemas import KeywordCreate, KeywordUpdate, KeywordResponse
from app.keywords import service
from app.projects import service as project_service

router = APIRouter(prefix="/keywords", tags=["Keywords"])

@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    keyword_in: KeywordCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership before adding a keyword
    project = await project_service.get_project(db=db, project_id=keyword_in.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return await service.create_keyword(db=db, keyword_in=keyword_in)

@router.get("", response_model=List[KeywordResponse])
async def read_keywords(
    project_id: Optional[uuid.UUID] = None, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if project_id:
        project = await project_service.get_project(db=db, project_id=project_id, owner_id=current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return await service.get_keywords(db=db, project_id=project_id)

@router.get("/{id}", response_model=KeywordResponse)
async def read_keyword(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = await service.get_keyword(db=db, keyword_id=id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
        
    # Check project ownership
    project = await project_service.get_project(db=db, project_id=keyword.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    return keyword

@router.put("/{id}", response_model=KeywordResponse)
async def update_keyword(
    id: uuid.UUID, 
    keyword_in: KeywordUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = await service.get_keyword(db=db, keyword_id=id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
        
    project = await project_service.get_project(db=db, project_id=keyword.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to modify this resource")
        
    return await service.update_keyword(db=db, db_keyword=keyword, keyword_in=keyword_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = await service.get_keyword(db=db, keyword_id=id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
        
    project = await project_service.get_project(db=db, project_id=keyword.project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resource")
        
    await service.delete_keyword(db=db, db_keyword=keyword)
    return None