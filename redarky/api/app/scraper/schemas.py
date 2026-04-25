from pydantic import BaseModel
from typing import List


class ScrapeRequest(BaseModel):
    query: str
    subreddits: List[str]


class ScrapedItem(BaseModel):
    source: str
    external_id: str
    title: str
    content: str | None = None
    url: str
    author: str | None = None
    score: int | None = 0
    scraped_at: str