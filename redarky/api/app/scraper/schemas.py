"""
app/scraper/schemas.py  — updated to match the new Go ScrapeRequest/ScrapeResult.
"""
 
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
 
 
class ScraperRunRequest(BaseModel):
    """Body accepted by POST /scraper/run (FastAPI → Go)."""
    project_id: UUID
 
    # Optional manual override for the lookback window (Unix timestamp).
    # If omitted, the Go service defaults to (now - 5 min) for live mode.
    since_timestamp: Optional[int] = None
 
    # If true, runs a 30-day backfill instead of a live poll.
    backfill: bool = False
 
 
class ScrapedItem(BaseModel):
    """
    Normalised record returned by the Go scraper.
    Must match models.ScrapedItem in Go exactly.
    """
    model_config = ConfigDict(extra="ignore")
 
    source: str                          # "reddit" | "hn"
    external_id: str
    title: str
    content: Optional[str] = ""
    url: str
    author: Optional[str] = "unknown"
    score: Optional[int] = 0
    subreddit: Optional[str] = ""       # "" for HN
    post_type: Optional[str] = "post"   # "post" | "comment"
    matched_keyword: Optional[str] = "" # which keyword triggered this hit
    is_brand_mention: Optional[bool] = False
    created_at: Optional[int] = None    # Unix timestamp of original creation
    scraped_at: datetime
 
 
class SourceError(BaseModel):
    source: str
    query: str
    message: str
 
 
class GoScrapeResult(BaseModel):
    """Full response from POST /scrape on the Go service."""
    items: List[ScrapedItem] = []
    errors: List[SourceError] = []
 
 