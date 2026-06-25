import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.leads.models import LeadStatus
from app.leads.schemas import LeadCreate, LeadStatusUpdate, LeadResponse
from app.leads import service

router = APIRouter(prefix="/leads", tags=["Leads"])

# GET /leads (with query filters)
@router.get("", response_model=List[LeadResponse])
async def read_leads(
    project_id: Optional[uuid.UUID] = None,
    status: Optional[LeadStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.get_leads(db=db, project_id=project_id, status=status)

# GET /leads/{id}
@router.get("/{id}", response_model=LeadResponse)
async def read_lead(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = await service.get_lead(db=db, lead_id=id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# PATCH /leads/{id}/status
@router.patch("/{id}/status", response_model=LeadResponse)
async def update_lead_status(
    id: uuid.UUID,
    status_in: LeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = await service.get_lead(db=db, lead_id=id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return await service.update_lead_status(db=db, db_lead=lead, status_in=status_in)

# DELETE /leads/{id}
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = await service.get_lead(db=db, lead_id=id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await service.delete_lead(db=db, db_lead=lead)
    return None

@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead_in: LeadCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await service.create_lead(db=db, lead_in=lead_in)