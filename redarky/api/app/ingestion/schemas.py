
# ── Pydantic models ────────────────────────────────────────────────────────────
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.database import get_db
from app.posts.models import Post
from app.ingestion import service as ingestion_service
from app.workers.matching_tasks import run_keyword_matching

class ScrapedItem(BaseModel):
    """
    Matches the output schema of the Apify Reddit actor (src/reddit.js).
    Fields map directly to the Post SQLAlchemy model.
    """
    model_config = ConfigDict(extra="ignore")

    source: str                             # "reddit"
    external_id: str
    title: str = ""
    content: str = ""
    author: str = "unknown"
    url: str
    score: int = 0
    comments_count: int = 0
    post_type: str = "post"                 # "post" | "comment"
    subreddit: str = ""
    created_at_platform: Optional[int] = None  # Unix timestamp


class RunStats(BaseModel):
    total_items: int = 0
    posts: int = 0
    comments: int = 0
    request_count: int = 0
    duration_ms: int = 0
    errors: list[str] = []


class ApifyWebhookPayload(BaseModel):
    """Body sent by the Apify actor's sendWebhook() call."""
    model_config = ConfigDict(extra="ignore")

    source_run_id: str = ""       # Apify run ID or our sourceRunId input
    project_id: str = ""          # which Redarky project this was for
    subreddits: list[str] = []
    items: list[ScrapedItem] = []
    stats: RunStats = RunStats()

