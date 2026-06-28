"""
app/workers/scraper_tasks.py

Celery tasks responsible for driving the Go scraper on a per-project schedule.

Architecture:
  - poll_project_live()  → runs every N minutes per active project (Celery Beat)
  - backfill_project()   → runs once on project creation to seed history
  - process_batch()      → existing task: dedup + insert into DB (unchanged)

Polling cadence:
  Beat schedule sends poll_project_live to a dedicated "scraper" queue.
  Each project polls independently so one slow project doesn't block others.
"""

import time
import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx

from app.workers.celery_app import celery
from app.workers.tasks import process_batch
from app.config import settings
from app.storage.local_s3 import LocalS3Storage

logger = logging.getLogger("celery.scraper")
storage = LocalS3Storage()

# How far back to look on each live poll (seconds).
# Set to slightly more than the poll interval so we never miss posts
# between two polls (e.g. poll every 5 min, window = 6 min).
LIVE_WINDOW_SECONDS = 6 * 60  # 6 minutes


# ── Live poll task ─────────────────────────────────────────────────────────────

@celery.task(
    name="scraper.poll_project_live",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds between retries
    queue="scraper",
)
def poll_project_live(self, project_id: str, include_keywords: list[str],
                      exclude_keywords: list[str], brand_keywords: list[str],
                      platforms: list[str], subreddits: list[str]) -> dict:
    """
    Called by Celery Beat every N minutes for each active project.

    Sends one request to the Go scraper covering the last LIVE_WINDOW_SECONDS,
    then hands the result off to process_batch for dedup + DB insert.

    The `since` timestamp is set to (now - LIVE_WINDOW_SECONDS) so we catch
    everything since the last poll, with a small overlap buffer.
    """
    since = int(time.time()) - LIVE_WINDOW_SECONDS

    logger.info(
        "Live poll starting",
        extra={"project_id": project_id, "since": since, "keywords": include_keywords},
    )

    payload = _build_go_payload(
        project_id=project_id,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        brand_keywords=brand_keywords,
        platforms=platforms,
        subreddits=subreddits,
        since=since,
        mode="live",
    )

    try:
        result = _call_go_scraper(payload)
    except Exception as exc:
        logger.error("Go scraper call failed: %s", exc, extra={"project_id": project_id})
        raise self.retry(exc=exc)

    items = result.get("items") or []
    errors = result.get("errors") or []

    if errors:
        for e in errors:
            logger.warning(
                "Scraper partial error: source=%s query=%s msg=%s",
                e.get("source"), e.get("query"), e.get("message"),
            )

    if not items:
        logger.info("Live poll: 0 new items", extra={"project_id": project_id})
        return {"items_fetched": 0}

    file_path = storage.write_json(
        layer="raw",
        mission_id=project_id,
        payload=items,
    )

    # Fire-and-forget: process_batch handles dedup + DB insert asynchronously.
    process_batch.delay(project_id, file_path)

    logger.info(
        "Live poll complete",
        extra={"project_id": project_id, "items": len(items), "file": file_path},
    )
    return {"items_fetched": len(items), "file_path": file_path}


# ── Backfill task ──────────────────────────────────────────────────────────────

@celery.task(
    name="scraper.backfill_project",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="scraper",
)
def backfill_project(self, project_id: str, include_keywords: list[str],
                     exclude_keywords: list[str], brand_keywords: list[str],
                     platforms: list[str], subreddits: list[str],
                     days_back: int = 30) -> dict:
    """
    Run once when a project is created to seed historical data.
    Uses `mode=backfill` which tells the Go scraper to use relevance sort
    and a longer time window.
    """
    since = int(time.time()) - (days_back * 24 * 60 * 60)

    logger.info(
        "Backfill starting",
        extra={"project_id": project_id, "days_back": days_back},
    )

    payload = _build_go_payload(
        project_id=project_id,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        brand_keywords=brand_keywords,
        platforms=platforms,
        subreddits=subreddits,
        since=since,
        mode="backfill",
    )

    try:
        result = _call_go_scraper(payload)
    except Exception as exc:
        logger.error("Backfill Go scraper failed: %s", exc, extra={"project_id": project_id})
        raise self.retry(exc=exc)

    items = result.get("items") or []

    if not items:
        logger.info("Backfill: 0 items found", extra={"project_id": project_id})
        return {"items_fetched": 0}

    file_path = storage.write_json(
        layer="raw",
        mission_id=project_id,
        payload=items,
    )
    process_batch.delay(project_id, file_path)

    logger.info(
        "Backfill complete",
        extra={"project_id": project_id, "items": len(items)},
    )
    return {"items_fetched": len(items), "file_path": file_path}


# ── Celery Beat schedule registration ─────────────────────────────────────────
#
# This is NOT a periodic task with a fixed schedule because each project
# can have a different poll interval. Instead, when a project is activated,
# Python schedules a recurring PeriodicTask via django-celery-beat (or
# equivalent) pointing at poll_project_live with that project's kwargs.
#
# If you're using celery beat with a static beat_schedule dict, you can
# add entries dynamically by calling celery.conf.beat_schedule at runtime,
# or — better — use the database-backed scheduler (celery-beat-django or
# redbeat) so you can add/remove schedules without restarting the worker.
#
# Example using redbeat (recommended):
#
#   from redbeat import RedBeatSchedulerEntry
#   import celery.schedules
#
#   entry = RedBeatSchedulerEntry(
#       name=f"poll:{project_id}",
#       task="scraper.poll_project_live",
#       schedule=celery.schedules.schedule(run_every=300),  # every 5 min
#       kwargs={
#           "project_id": str(project_id),
#           "include_keywords": [...],
#           ...
#       },
#       app=celery,
#   )
#   entry.save()
#
# To cancel when a project is paused/deleted:
#   entry = RedBeatSchedulerEntry.from_key(f"redbeat:poll:{project_id}", app=celery)
#   entry.delete()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_go_payload(
    project_id: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
    brand_keywords: list[str],
    platforms: list[str],
    subreddits: list[str],
    since: int,
    mode: str,
) -> dict:
    return {
        "project_id": project_id,
        "include_keywords": include_keywords,
        "exclude_keywords": exclude_keywords,
        "brand_keywords": brand_keywords,
        "platforms": platforms,
        "subreddits": subreddits,
        "since": since,
        "mode": mode,
    }


def _call_go_scraper(payload: dict) -> dict:
    """
    Sends a POST /scrape to the Go microservice and returns the parsed JSON.
    Raises on HTTP error or timeout.
    """
    url = settings.GO_SCRAPER_URL
    if not url.endswith("/scrape"):
        url = f"{url}/scrape"

    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()