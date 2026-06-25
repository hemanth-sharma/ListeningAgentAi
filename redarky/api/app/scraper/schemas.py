from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ScraperRunRequest(BaseModel):
    project_id: UUID
    # Optional field to override lookback window manually (Unix Timestamp)
    since_timestamp: Optional[int] = None

class GoScraperPayload(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    platforms: List[str] = Field(default_factory=list)
    subreddits: List[str] = Field(default_factory=list)
    since: int = Field(description="Unix timestamp floor boundary")

class ScrapedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str
    title: str
    content: Optional[str] = ""
    url: str
    author: Optional[str] = "unknown"
    score: Optional[int] = 0
    scraped_at: datetime