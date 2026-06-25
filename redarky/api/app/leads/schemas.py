from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.leads.models import LeadStatus

class LeadBase(BaseModel):
    status: LeadStatus = LeadStatus.NEW
    buying_intent_score: float
    reason: str
    url: str
    created_at_platform: Optional[str] = None

class LeadCreate(LeadBase):
    project_id: UUID
    post_id: UUID

class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    buying_intent_score: Optional[float] = None
    reason: Optional[str] = None
    url: Optional[str] = None

class LeadStatusUpdate(BaseModel):
    status: LeadStatus

class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    post_id: UUID
    created_at: datetime
    updated_at: datetime