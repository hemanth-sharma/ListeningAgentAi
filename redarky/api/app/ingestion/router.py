"""
app/ingestion/router.py

FastAPI endpoint that receives the webhook POST from the Apify Reddit actor.

This is the fast path:
  Apify actor finishes → POSTs to /ingestion/reddit → we dedup + insert → keyword match

The endpoint is designed to be:
  - Fast: all heavy work (keyword matching, lead scoring) is offloaded to Celery
  - Idempotent: safe to receive the same payload twice (ON CONFLICT DO NOTHING)
  - Non-blocking: returns 200 immediately, processes async

Security: The endpoint checks a shared secret header (X-Redarky-Secret) that
matches APIFY_WEBHOOK_SECRET in your .env. Set this same value in the Apify
actor's webhookUrl as a query param or in the actor input.
"""

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
from app.ingestion.schemas import ScrapedItem, RunStats, ApifyWebhookPayload
from app.workers.matching_tasks import run_keyword_matching
logger = logging.getLogger("uvicorn.ingestion")

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/reddit", status_code=status.HTTP_200_OK)
async def ingest_reddit(
    payload: ApifyWebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_redarky_secret: str = Header(default="some-long-random-string"),
):
    """
    Receives scraped items from the Apify Reddit actor.

    Steps:
      1. Validate shared secret
      2. Bulk-insert items into raw_posts (global dedup table)
      3. Kick off background keyword matching task
      4. Return immediately

    The keyword matching (which project's keywords match these posts)
    runs in the background so this endpoint stays fast.
    """
    # ── Auth ──────────────────────────────────────────────────────────────────
    if x_redarky_secret != settings.APIFY_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    if not payload.items:
        return {"accepted": 0, "message": "No items in payload"}

    # ── Bulk insert into raw_posts ────────────────────────────────────────────
    inserted_ids, skipped = await ingestion_service.bulk_upsert_raw_posts(
        db=db,
        items=payload.items,
        source_run_id=payload.source_run_id,
    )

    logger.info(
        "Reddit ingestion: inserted=%d skipped=%d run=%s",
        len(inserted_ids), skipped, payload.source_run_id
    )

    # ── Kick off keyword matching in background ───────────────────────────────
    # Pass the raw_post IDs that were actually new (not dupes) so the matching
    # task only processes genuinely new items.
    if inserted_ids:
        background_tasks.add_task(
            _trigger_keyword_matching,
            raw_post_ids=inserted_ids,
            source_run_id=payload.source_run_id,
        )

    return {
        "accepted": len(inserted_ids),
        "skipped_dupes": skipped,
        "source_run_id": payload.source_run_id,
    }


async def _trigger_keyword_matching(raw_post_ids: list[str], source_run_id: str):
    """Fires the Celery keyword matching task after the HTTP response is sent."""
    try:
        run_keyword_matching.delay(
            raw_post_ids=[str(i) for i in raw_post_ids],
            source_run_id=source_run_id,
        )
    except Exception as e:
        logger.error("Failed to queue keyword matching task: %s", e)