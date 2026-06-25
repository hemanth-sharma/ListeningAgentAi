from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ScraperRunRequest(BaseModel):
    project_id: UUID

class GoScraperPayload(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    subreddits: List[str] = Field(default_factory=list)

class ScrapedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str
    title: str
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    score: Optional[int] = 0
    scraped_at: datetime