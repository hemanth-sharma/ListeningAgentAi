"""
app/ingestion/service.py

Database operations for the ingestion layer.

Handles:
  - Bulk upserting scraped items into raw_posts (global dedup table)
  - TTL management (expires_at for automatic cleanup)
  - Returning only newly inserted IDs so keyword matching skips dupes
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from app.ingestion.models import RawPost, KeywordMatch


from app.database import Base

logger = logging.getLogger("uvicorn.ingestion")

# How long to keep raw posts before deleting them.
# 7 days gives enough window for the AI scoring pipeline to process everything
# without keeping a large permanent archive.
RAW_POST_TTL_DAYS = 7


# ── Model ──────────────────────────────────────────────────────────────────────


# ── Service functions ──────────────────────────────────────────────────────────

async def bulk_upsert_raw_posts(
    db: AsyncSession,
    items: list,
    source_run_id: str,
) -> tuple[list[uuid.UUID], int]:
    """
    Bulk-inserts scraped items into raw_posts.
    Uses ON CONFLICT DO NOTHING so duplicate items (seen on a previous run)
    are silently skipped.

    Returns:
      - list of UUIDs for newly inserted rows (for keyword matching)
      - count of skipped duplicates
    """
    # Changed to timezone-naive UTC to match the other models and DB schema
    now = datetime.utcnow()
    # now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=RAW_POST_TTL_DAYS)

    inserted_ids = []
    skipped = 0

    # Insert one by one with RETURNING to get new IDs.
    # Batch insert with RETURNING is complex with ON CONFLICT — individual
    # inserts keep the logic simple and are fast enough for 100-200 items.
    for item in items:
        stmt = (
            pg_insert(RawPost)
            .values(
                id=uuid.uuid4(),
                source=item.source,
                external_id=item.external_id,
                source_run_id=source_run_id,
                title=item.title or "",
                content=item.content or "",
                author=item.author or "unknown",
                url=item.url,
                score=item.score or 0,
                comments_count=item.comments_count or 0,
                post_type=item.post_type or "post",
                subreddit=item.subreddit or "",
                created_at_platform=item.created_at_platform,
                fetched_at=now,
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(
                index_elements=["source", "external_id"]
            )
            .returning(RawPost.id)
        )

        result = await db.execute(stmt)
        new_id = result.scalar_one_or_none()

        if new_id:
            inserted_ids.append(new_id)
        else:
            skipped += 1

    await db.commit()
    return inserted_ids, skipped


async def cleanup_expired_raw_posts(db: AsyncSession) -> int:
    """
    Deletes raw_posts rows past their expires_at date.
    Run this as a nightly Celery Beat task to keep the table small.

    Cascade deletes keyword_matches rows for the same posts automatically
    (via the FK ondelete=CASCADE on keyword_matches.raw_post_id).

    Returns the count of deleted rows.
    """
    from sqlalchemy import delete, func
    # now = datetime.now(timezone.utc)
    now = datetime.utcnow()

    result = await db.execute(
        delete(RawPost).where(RawPost.expires_at < now).returning(RawPost.id)
    )
    deleted_count = len(result.fetchall())
    await db.commit()

    logger.info("TTL cleanup: deleted %d expired raw_posts", deleted_count)
    return deleted_count