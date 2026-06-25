import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User 

from app.projects.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.projects import service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.create_project(db=db, project_in=project_in, owner_id=current_user.id)

@router.get("", response_model=List[ProjectResponse])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.get_projects(db=db, owner_id=current_user.id)

@router.get("/{id}", response_model=ProjectResponse)
async def read_project(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await service.get_project(db=db, project_id=id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{id}", response_model=ProjectResponse)
async def update_project(
    id: uuid.UUID, 
    project_in: ProjectUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await service.get_project(db=db, project_id=id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await service.update_project(db=db, db_project=project, project_in=project_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await service.get_project(db=db, project_id=id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await service.delete_project(db=db, db_project=project)
    return None