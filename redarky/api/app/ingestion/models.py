
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RawPost(Base):
    """
    Global shared table — one row per unique (source, external_id) across
    ALL projects and users. This is the key to the shared-scraping architecture:
    100 users watching r/forhire = the same posts live here once.

    Projects are linked via keyword_matches (not a FK here).
    """
    __tablename__ = "raw_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source identity
    source: Mapped[str] = mapped_column(String(32), nullable=False)          # "reddit" | "hn"
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)    # e.g. "1abc2de"
    source_run_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # The Apify run ID that produced this row — useful for debugging

    # Content
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Engagement
    score: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    comments_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Classification
    post_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # "post" | "comment"
    subreddit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at_platform: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Set to fetched_at + RAW_POST_TTL_DAYS. Nightly cleanup deletes expired rows.

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_raw_post_source_external_id"),
    )


class KeywordMatch(Base):
    """
    Links a raw_post to a specific project when that post matched one of the
    project's keywords. This is how the global raw_posts table becomes
    per-user results.

    One raw_post can have many KeywordMatch rows (multiple projects, multiple keywords).
    """
    __tablename__ = "keyword_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    matched_keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "include" | "brand"
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # False = AI scoring hasn't run yet. True = lead was created or item was rejected.
    matched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Prevent duplicate matches: same post + same project + same keyword
        UniqueConstraint("raw_post_id", "project_id", "matched_keyword",
                         name="uq_keyword_match_post_project_keyword"),
    )
