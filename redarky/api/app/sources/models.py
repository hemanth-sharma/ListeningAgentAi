"""
app/sources/models.py + app/sources/service.py

monitored_sources: global registry of subreddits being scraped.
project_sources: join table linking projects to their watched subreddits.

The subscriber_count pattern is what keeps scraping costs proportional
to unique sources, not to user count.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, select, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.apify.scheduler import (
    create_subreddit_schedule,
    pause_subreddit_schedule,
    resume_subreddit_schedule,
    trigger_immediate_run,
)

logger = logging.getLogger("uvicorn.sources")


# ── Models ─────────────────────────────────────────────────────────────────────

class MonitoredSource(Base):
    """
    One row per unique (source_type, identifier) combination being actively scraped.
    e.g. ("reddit", "forhire"), ("reddit", "devops"), ("hn", "frontpage")

    Shared across all users. 1000 users watching r/forhire = 1 row here.
    """
    __tablename__ = "monitored_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)        # "reddit" | "hn"
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)        # subreddit name | "frontpage"
    interval_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Number of active projects watching this source.
    # When this hits 0, we pause the Apify schedule to stop paying for it.

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    apify_schedule_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # The Apify schedule ID so we can pause/resume it programmatically.

    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_type", "identifier", name="uq_monitored_source"),
    )


class ProjectSource(Base):
    """
    Join table: which subreddits (monitored_sources) does each project watch?
    When a user adds r/forhire to their project, we add a row here and
    increment monitored_sources.subscriber_count.
    """
    __tablename__ = "project_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    monitored_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monitored_sources.id", ondelete="CASCADE"), nullable=False
    )
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    # Denormalised copy of monitored_sources.identifier for fast keyword matching queries.
    # Avoids a join in the hot matching path.

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "monitored_source_id", name="uq_project_source"),
    )

