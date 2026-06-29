import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SubredditAddRequest(BaseModel):
    subreddit: str

class MonitoredSourceResponse(BaseModel):
    id: uuid.UUID
    source_type: str
    identifier: str
    interval_minutes: int
    subscriber_count: int
    is_active: bool
    apify_schedule_id: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)