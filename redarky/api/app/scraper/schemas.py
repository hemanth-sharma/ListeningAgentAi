from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ScrapeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    subreddits: List[str] = Field(default_factory=list)


class ScrapedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str
    title: str
    content: str | None = None
    url: str
    author: str | None = None
    score: int | None = 0
    scraped_at: datetime