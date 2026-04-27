from datetime import datetime

from pydantic import BaseModel, ConfigDict
from uuid import UUID

class MissionCreate(BaseModel):
    name: str
    goal: str


class MissionUpdate(BaseModel):
    name: str | None = None
    goal: str | None = None
    status: str | None = None


class MissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    goal: str
    status: str
    created_at: datetime
    updated_at: datetime