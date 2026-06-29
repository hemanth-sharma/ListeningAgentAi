"""
app/apify/scheduler.py

Manages Apify actor schedules for monitored subreddits.

This is what replaces Celery Beat for the scraping layer.
Instead of Celery triggering Go every 5 minutes, Apify's own scheduler
triggers our Reddit actor every 30 minutes — and Apify handles the
infrastructure (compute, proxy rotation, retries) for us.

When a user adds r/forhire to their project:
  1. We check if monitored_sources already has a row for reddit:forhire
  2. If yes → increment subscriber_count, done
  3. If no → create the monitored_sources row + create an Apify schedule
     that fires the actor every 30 minutes with r/forhire as input

When the last user removes r/forhire from their project:
  1. subscriber_count hits 0
  2. We delete (or pause) the Apify schedule
  3. Stop paying for scraping a source nobody cares about

This keeps scraping cost proportional to the number of unique sources
being monitored — not the number of users or projects.
"""

import httpx
import logging
import json
from uuid import UUID

from app.config import settings

logger = logging.getLogger("uvicorn.apify")

# Apify API base URL
APIFY_API_BASE = "https://api.apify.com/v2"

# Your Actor ID from Apify Console (set APIFY_REDDIT_ACTOR_ID in .env)
# Format: "yourusername/redarky-reddit-scraper"
REDDIT_ACTOR_ID = settings.APIFY_REDDIT_ACTOR_ID

# Shared secret sent in the webhook payload header so your ingestion
# endpoint can verify the request came from the actor
WEBHOOK_SECRET = settings.APIFY_WEBHOOK_SECRET

# Your FastAPI ingestion endpoint URL (publicly reachable)
INGESTION_WEBHOOK_URL = settings.APIFY_WEBHOOK_URL  # e.g. "https://api.redarky.com/ingestion/reddit"


async def create_subreddit_schedule(
    subreddit: str,
    source_id: UUID,
    interval_minutes: int = 30,
) -> str | None:
    """
    Creates an Apify schedule that runs the Reddit actor every N minutes
    for a single subreddit.

    Returns the Apify schedule ID (stored in monitored_sources.apify_schedule_id)
    or None if creation failed.

    The actor input is fixed at schedule creation time. Each subreddit gets
    its own schedule so we can independently pause/delete them.

    @param subreddit: subreddit name without "r/" prefix
    @param source_id: our monitored_sources UUID, passed through to the webhook
    @param interval_minutes: how often to run (30 for standard, 10 for live tier)
    """
    # Cron expression for "every N minutes"
    # Apify schedules use standard cron: "*/30 * * * *" = every 30 minutes
    cron_expression = f"*/{interval_minutes} * * * *"

    # The actor input that will be sent on each scheduled run
    actor_input = {
        "subreddits": [subreddit],
        # sinceTimestamp = 0 means the actor defaults to (now - 35 min)
        # which is slightly longer than the interval to avoid missing posts
        "sinceTimestamp": 0,
        "postsPerSubreddit": 100,
        "fetchComments": True,
        "commentsPerSubreddit": 100,
        "webhookUrl": INGESTION_WEBHOOK_URL,
        # source_id lets the backend correlate this run to a monitored_sources row
        "sourceRunId": str(source_id),
    }

    schedule_payload = {
        "name": f"redarky-reddit-{subreddit}",
        "cronExpression": cron_expression,
        "timezone": "UTC",
        "isEnabled": True,
        "isExclusive": True,  # don't start a new run if previous is still running
        "actions": [
            {
                "type": "RUN_ACTOR",
                "actorId": REDDIT_ACTOR_ID,
                "input": actor_input,
                # Use minimum memory since we're doing lightweight HTTP only
                "options": {
                    "memoryMbytes": 256,
                },
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{APIFY_API_BASE}/schedules",
                json=schedule_payload,
                headers={"Authorization": f"Bearer {settings.APIFY_API_TOKEN}"},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            schedule_id = data["data"]["id"]
            logger.info("Created Apify schedule %s for r/%s", schedule_id, subreddit)
            return schedule_id

        except Exception as e:
            logger.error("Failed to create Apify schedule for r/%s: %s", subreddit, e)
            return None


async def pause_subreddit_schedule(apify_schedule_id: str, subreddit: str) -> bool:
    """
    Pauses an existing Apify schedule (when subscriber_count hits 0).
    Pausing is preferable to deleting — we can re-enable it if a new user
    adds the same subreddit later without recreating the schedule.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{APIFY_API_BASE}/schedules/{apify_schedule_id}/pause",
                headers={"Authorization": f"Bearer {settings.APIFY_API_TOKEN}"},
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info("Paused Apify schedule %s (r/%s)", apify_schedule_id, subreddit)
            return True
        except Exception as e:
            logger.error("Failed to pause schedule %s: %s", apify_schedule_id, e)
            return False


async def resume_subreddit_schedule(apify_schedule_id: str, subreddit: str) -> bool:
    """Re-enables a previously paused schedule."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{APIFY_API_BASE}/schedules/{apify_schedule_id}/resume",
                headers={"Authorization": f"Bearer {settings.APIFY_API_TOKEN}"},
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info("Resumed Apify schedule %s (r/%s)", apify_schedule_id, subreddit)
            return True
        except Exception as e:
            logger.error("Failed to resume schedule %s: %s", apify_schedule_id, e)
            return False


async def trigger_immediate_run(subreddit: str, source_id: UUID) -> str | None:
    """
    Triggers a one-off actor run immediately (not via schedule).
    Used when a user first adds a subreddit — we run a backfill immediately
    rather than waiting for the next scheduled interval.

    Returns the Apify run ID or None on failure.
    """
    actor_input = {
        "subreddits": [subreddit],
        "sinceTimestamp": 0,    # 0 = actor defaults to (now - 35 min) for live mode
        "postsPerSubreddit": 100,
        "fetchComments": True,
        "commentsPerSubreddit": 100,
        "webhookUrl": INGESTION_WEBHOOK_URL,
        "sourceRunId": str(source_id),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{APIFY_API_BASE}/acts/{REDDIT_ACTOR_ID}/runs",
                json=actor_input,
                params={"memory": 256},
                headers={"Authorization": f"Bearer {settings.APIFY_API_TOKEN}"},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            run_id = data["data"]["id"]
            logger.info("Triggered immediate run %s for r/%s", run_id, subreddit)
            return run_id
        except Exception as e:
            logger.error("Failed to trigger immediate run for r/%s: %s", subreddit, e)
            return None