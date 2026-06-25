from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: str

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime