from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class PostBase(BaseModel):
    platform: str
    external_id: str
    title: str
    content: str
    author: str
    url: str
    score: Optional[float] = None
    comments_count: Optional[int] = None
    created_at_platform: Optional[str] = None

class PostCreate(PostBase):
    project_id: UUID

class PostUpdate(PostBase):
    pass

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime