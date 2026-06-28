"""
app/workers/tasks.py

Updated process_batch to handle the new ScrapedItem fields:
  - post_type
  - subreddit
  - matched_keyword
  - is_brand_mention
  - created_at (Unix int) → created_at_platform
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.posts.models import Post
from app.scraper.schemas import ScrapedItem
from app.storage.local_s3 import LocalS3Storage
from app.utils.redis_client import is_duplicate
from app.workers.celery_app import celery


storage = LocalS3Storage()


def generate_post_hash(item: ScrapedItem) -> str:
    """
    Stable SHA-256 deduplication key.
    Uses source + external_id so the same Reddit post matched by two
    different keywords only gets stored once.
    """
    h = hashlib.sha256()
    h.update(item.source.encode("utf-8"))
    h.update(item.external_id.encode("utf-8"))
    return h.hexdigest()


@celery.task(name="batch.process", queue="default")
def process_batch(project_id: str, file_path: str) -> dict:
    """
    Reads a raw JSON file from local S3, deduplicates, and bulk-inserts
    into the posts table.

    Called by both poll_project_live and backfill_project after the Go
    scraper returns results.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.ensure_future(_process_batch_async(project_id, file_path))
    else:
        return asyncio.run(_process_batch_async(project_id, file_path))


async def _process_batch_async(project_id: str, file_path: str) -> dict:
    print(f"process_batch: project={project_id} file={file_path}")

    raw_data = storage.read_json(file_path)
    processed_payload = []
    dead_letter_payload = []
    inserted_count = 0
    skipped_count = 0

    async with SessionLocal() as db:
        for item_dict in raw_data:
            try:
                validated = ScrapedItem.model_validate(item_dict)

                # Redis dedup: same post matched by multiple keywords → skip
                hash_key = generate_post_hash(validated)
                if is_duplicate(project_id, hash_key):
                    skipped_count += 1
                    continue

                stmt = (
                    insert(Post)
                    .values(
                        project_id=UUID(project_id),
                        source=validated.source,
                        external_id=validated.external_id,
                        title=validated.title,
                        content=validated.content or "",
                        url=validated.url,
                        author=validated.author or "unknown",
                        score=validated.score or 0,

                        # ── New fields ────────────────────────────────────────
                        post_type=validated.post_type or "post",
                        subreddit=validated.subreddit or "",
                        matched_keyword=validated.matched_keyword or "",
                        is_brand_mention=validated.is_brand_mention or False,
                        created_at_platform=validated.created_at,  # Unix int from Go
                        # ─────────────────────────────────────────────────────

                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    .on_conflict_do_nothing(index_elements=["project_id", "external_id"])
                    .returning(Post.id)
                )

                result = await db.execute(stmt)
                inserted_id = result.scalar_one_or_none()

                if inserted_id:
                    inserted_count += 1
                    processed_payload.append(validated.model_dump(mode="json"))
                else:
                    skipped_count += 1

            except Exception as exc:
                dead_letter_payload.append({"item": item_dict, "error": str(exc)})
                print(f"process_batch: item failed: {exc}")

        await db.commit()

    if processed_payload:
        storage.write_json(layer="processed", mission_id=project_id, payload=processed_payload)
    if dead_letter_payload:
        storage.write_json(layer="dead-letter", mission_id=project_id, payload=dead_letter_payload)

    summary = {
        "project_id": project_id,
        "inserted": inserted_count,
        "skipped_dupes": skipped_count,
        "dead_letter": len(dead_letter_payload),
    }
    print(f"process_batch complete: {summary}")
    return summary