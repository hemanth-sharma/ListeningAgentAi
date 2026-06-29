from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.keywords.models import KeywordType

class KeywordBase(BaseModel):
    keyword: str
    keyword_type: KeywordType

class KeywordCreate(KeywordBase):
    project_id: UUID

class KeywordUpdate(KeywordBase):
    pass

class KeywordResponse(KeywordBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    created_at: datetime