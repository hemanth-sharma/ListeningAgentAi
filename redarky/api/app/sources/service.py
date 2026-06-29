
# ── Service functions ──────────────────────────────────────────────────────────
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
from app.sources.models import ProjectSource, MonitoredSource

logger = logging.getLogger("uvicorn.sources")



async def add_subreddit_to_project(
    db: AsyncSession,
    project_id: UUID,
    subreddit: str,
) -> MonitoredSource:
    """
    Called when a user adds a subreddit to their project from the dashboard.

    Steps:
      1. Get or create a MonitoredSource row for this subreddit
      2. If brand new: create an Apify schedule + trigger immediate run
      3. If existed but was paused: resume the Apify schedule
      4. Link the project to the source via ProjectSource
      5. Increment subscriber_count
    """
    subreddit = subreddit.lower().strip()

    # Step 1: get or create
    result = await db.execute(
        select(MonitoredSource).where(
            and_(
                MonitoredSource.source_type == "reddit",
                MonitoredSource.identifier == subreddit,
            )
        )
    )
    source = result.scalar_one_or_none()
    is_new = source is None

    if is_new:
        source = MonitoredSource(
            source_type="reddit",
            identifier=subreddit,
            interval_minutes=30,
            subscriber_count=0,
            is_active=False,  # set True after Apify schedule created
        )
        db.add(source)
        await db.flush()  # get the ID before async Apify call

    # Step 2/3: manage the Apify schedule
    if is_new:
        schedule_id = await create_subreddit_schedule(
            subreddit=subreddit,
            source_id=source.id,
            interval_minutes=30,
        )
        if schedule_id:
            source.apify_schedule_id = schedule_id
            source.is_active = True
            # Fire an immediate run so the user sees data right away
            await trigger_immediate_run(subreddit=subreddit, source_id=source.id)
        else:
            logger.error("Could not create Apify schedule for r/%s", subreddit)

    elif not source.is_active and source.apify_schedule_id:
        # Source exists but was paused — resume it
        resumed = await resume_subreddit_schedule(source.apify_schedule_id, subreddit)
        if resumed:
            source.is_active = True

    # Step 4: link project to source
    existing_link_result = await db.execute(
        select(ProjectSource).where(
            and_(
                ProjectSource.project_id == project_id,
                ProjectSource.monitored_source_id == source.id,
            )
        )
    )
    existing_link = existing_link_result.scalar_one_or_none()

    if not existing_link:
        link = ProjectSource(
            project_id=project_id,
            monitored_source_id=source.id,
            source_identifier=subreddit,
            is_active=True,
        )
        db.add(link)

        # Step 5: increment subscriber count
        source.subscriber_count += 1

    await db.commit()
    logger.info("Added r/%s to project %s (subscriber_count=%d)", subreddit, project_id, source.subscriber_count)
    return source


async def remove_subreddit_from_project(
    db: AsyncSession,
    project_id: UUID,
    subreddit: str,
) -> None:
    """
    Called when a user removes a subreddit from their project.

    If subscriber_count hits 0, pauses the Apify schedule so we stop
    paying for a source nobody is watching.
    """
    subreddit = subreddit.lower().strip()

    source_result = await db.execute(
        select(MonitoredSource).where(
            and_(
                MonitoredSource.source_type == "reddit",
                MonitoredSource.identifier == subreddit,
            )
        )
    )
    source = source_result.scalar_one_or_none()
    if not source:
        return

    # Remove the project link
    link_result = await db.execute(
        select(ProjectSource).where(
            and_(
                ProjectSource.project_id == project_id,
                ProjectSource.monitored_source_id == source.id,
            )
        )
    )
    link = link_result.scalar_one_or_none()
    if link:
        await db.delete(link)
        source.subscriber_count = max(0, source.subscriber_count - 1)

    # If nobody is watching this source anymore, pause the schedule
    if source.subscriber_count == 0 and source.apify_schedule_id:
        paused = await pause_subreddit_schedule(source.apify_schedule_id, subreddit)
        if paused:
            source.is_active = False
            logger.info("Paused r/%s schedule — no subscribers", subreddit)

    await db.commit()