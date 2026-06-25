import uuid
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.leads.models import Lead, LeadStatus
from app.leads.schemas import LeadCreate, LeadUpdate, LeadStatusUpdate

async def get_leads(
    db: AsyncSession, 
    project_id: Optional[uuid.UUID] = None,
    status: Optional[LeadStatus] = None
) -> Sequence[Lead]:
    stmt = select(Lead)
    
    if project_id:
        stmt = stmt.where(Lead.project_id == project_id)
    if status:
        stmt = stmt.where(Lead.status == status)
        
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_lead(db: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()

async def create_lead(db: AsyncSession, lead_in: LeadCreate) -> Lead:
    db_lead = Lead(**lead_in.model_dump())
    db.add(db_lead)
    await db.commit()
    await db.refresh(db_lead)
    return db_lead

async def update_lead_status(db: AsyncSession, db_lead: Lead, status_in: LeadStatusUpdate) -> Lead:
    db_lead.status = status_in.status
    await db.commit()
    await db.refresh(db_lead)
    return db_lead

async def delete_lead(db: AsyncSession, db_lead: Lead) -> None:
    await db.delete(db_lead)
    await db.commit()