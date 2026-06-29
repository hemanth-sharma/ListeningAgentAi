"""
app/workers/matching_tasks.py

Celery task that runs keyword matching after new posts are ingested.

This is the step that makes the shared-scraping architecture work:
  - raw_posts are global (one copy per post, across all users)
  - keyword_matches are per-project (which projects care about each post)

The matching logic is pure Python string operations — no API calls, no LLM.
It runs in milliseconds even for 100 posts × 500 keywords across 50 projects.

After this task creates keyword_matches rows, the AI scoring task picks up
only those rows (not all raw_posts) — keeping LLM costs minimal.
"""

import logging
import uuid
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import SessionLocal
from app.ingestion.service import RawPost, KeywordMatch
from app.keywords.models import Keyword, KeywordType
from app.sources.models import ProjectSource  # see note below
from app.workers.celery_app import celery
from app.posts.models import Post
from datetime import datetime


logger = logging.getLogger("celery.matching")


@celery.task(
    name="matching.run_keyword_matching",
    queue="matching",
    max_retries=3,
    default_retry_delay=10,
)
def run_keyword_matching(raw_post_ids: list[str], source_run_id: str = "") -> dict:
    """
    Given a list of newly inserted raw_post IDs, finds which project keywords
    match each post and creates keyword_matches rows.

    Called by the ingestion endpoint's background task immediately after
    bulk_upsert_raw_posts() returns.

    Returns a summary dict for logging.
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.ensure_future(_run_matching_async(raw_post_ids, source_run_id))
    else:
        return asyncio.run(_run_matching_async(raw_post_ids, source_run_id))



async def _run_matching_async(raw_post_ids: list[str], source_run_id: str) -> dict:
    if not raw_post_ids:
        return {"matches_created": 0, "posts_checked": 0}

    async with SessionLocal() as db:
        # ── 1. Load the raw posts we need to match ─────────────────────────────
        post_uuids = [UUID(pid) for pid in raw_post_ids]
        posts_result = await db.execute(
            select(RawPost).where(RawPost.id.in_(post_uuids))
        )
        posts = posts_result.scalars().all()

        if not posts:
            return {"matches_created": 0, "posts_checked": 0}

        # Gather unique subreddits from this batch so we can load only the
        # keywords from projects watching those subreddits.
        # subreddits_in_batch = {p.subreddit for p in posts if p.subreddit}
        # Create a set containing both original and lowercase variants of the subreddits
        subreddits_in_batch = set()
        for p in posts:
            if p.subreddit:
                subreddits_in_batch.add(p.subreddit)
                subreddits_in_batch.add(p.subreddit.lower())
                subreddits_in_batch.add(p.subreddit.capitalize())

        # ── 2. Load all active keywords for projects watching these subreddits ──
        #
        # ProjectSource is a join table: project_id ↔ source_identifier (subreddit name).
        # We only load keywords from projects that are actually watching the
        # subreddits in this batch — avoids loading the entire keywords table.
        keywords_result = await db.execute(
            select(Keyword)
            .join(ProjectSource, ProjectSource.project_id == Keyword.project_id)
            .where(
                and_(
                    ProjectSource.source_identifier.in_(subreddits_in_batch),
                    ProjectSource.is_active == True,
                    Keyword.keyword_type.in_([KeywordType.INCLUDE.value, KeywordType.BRAND.value]),
                )
            )
        )
        keywords = keywords_result.scalars().all()

        if not keywords:
            logger.info("No active keywords found for subreddits: %s", subreddits_in_batch)
            return {"matches_created": 0, "posts_checked": len(posts)}

        # Load exclude keywords separately (we need them per-project)
        excludes_result = await db.execute(
            select(Keyword).where(
                and_(
                    Keyword.project_id.in_({kw.project_id for kw in keywords}),
                    Keyword.keyword_type == KeywordType.EXCLUDE.value, # <-- Fix here as well
                )
            )
        )
        exclude_keywords = excludes_result.scalars().all()

        # Build lookup maps for O(1) access during the matching loop
        # project_id → list of exclude keyword strings
        project_excludes: dict[UUID, list[str]] = {}
        for kw in exclude_keywords:
            project_excludes.setdefault(kw.project_id, []).append(kw.keyword.lower())

        # ── 3. Match posts against keywords in memory ──────────────────────────
        #
        # This is the entire matching algorithm: two nested loops, pure Python.
        # For 100 posts × 200 keywords = 20,000 string comparisons.
        # Python can do ~5 million string contains checks per second.
        # This runs in well under 10ms.

        matches_to_create = []

        for post in posts:
            # Build the searchable text for this post once
            searchable = (
                (post.title or "") + " " + (post.content or "")
            ).lower()

            # Skip empty posts (link posts with no selftext)
            if len(searchable.strip()) < 20:
                continue

            for kw in keywords:
                kw_lower = kw.keyword.lower()

                # Check include/brand keyword is present
                if kw_lower not in searchable:
                    continue

                # Check no exclude keyword is present for this project
                project_exclude_list = project_excludes.get(kw.project_id, [])
                if any(ex in searchable for ex in project_exclude_list):
                    continue

                matches_to_create.append({
                    "raw_post_id": post.id,
                    "project_id": kw.project_id,
                    "matched_keyword": kw.keyword,
                    "match_type": kw.keyword_type.value,  # "include" | "brand"
                    "is_processed": False,
                })

        # ── 4. Bulk insert keyword_matches ─────────────────────────────────────
        matches_created = 0
        for match_data in matches_to_create:
            # First, preserve the core engineering architecture record
            stmt = (
                pg_insert(KeywordMatch)
                .values(**match_data)
                .on_conflict_do_nothing(
                    index_elements=["raw_post_id", "project_id", "matched_keyword"]
                )
                .returning(KeywordMatch.id)
            )
            result = await db.execute(stmt)
            
            if result.scalar_one_or_none():
                matches_created += 1
                
                # BINDING STEP: Instantly push this to the user's Post dashboard feed
                # Find the corresponding post object from your memory-resident batch array
                matching_raw_post = next(p for p in posts if p.id == match_data["raw_post_id"])
                
                post_feed_stmt = (
                    pg_insert(Post)
                    .values(
                        id=uuid.uuid4(),
                        project_id=match_data["project_id"],
                        source=matching_raw_post.source,
                        external_id=matching_raw_post.external_id,
                        title=matching_raw_post.title,
                        content=matching_raw_post.content,
                        author=matching_raw_post.author,
                        url=matching_raw_post.url,
                        score=matching_raw_post.score,
                        comments_count=matching_raw_post.comments_count,
                        post_type=matching_raw_post.post_type,
                        subreddit=matching_raw_post.subreddit,
                        matched_keyword=match_data["matched_keyword"],
                        is_brand_mention=(match_data["match_type"] == "brand"),
                        created_at_platform=matching_raw_post.created_at_platform,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    .on_conflict_do_nothing(
                        index_elements=["project_id", "external_id"]
                    )
                )
                await db.execute(post_feed_stmt)

        await db.commit()

        logger.info(
            "Keyword matching complete: %d posts → %d matches created (run=%s)",
            len(posts), matches_created, source_run_id,
        )

        return {
            "matches_created": matches_created,
            "posts_checked": len(posts),
            "keywords_checked": len(keywords),
            "source_run_id": source_run_id,
        }