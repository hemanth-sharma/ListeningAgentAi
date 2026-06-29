from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class PostBase(BaseModel):
    source: str  
    external_id: str
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    url: str
    score: Optional[int] = 0
    comments_count: Optional[int] = 0
    # FIX: Must match BigInteger/Optional[int] coming from Go/Apify
    created_at_platform: Optional[int] = None


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