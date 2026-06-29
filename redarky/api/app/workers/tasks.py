# app/workers/tasks.py
import asyncio
from datetime import datetime, timezone
from uuid import UUID

from app.database import SessionLocal
from app.ingestion.service import bulk_upsert_raw_posts # Import your raw_posts bulk service
from app.scraper.schemas import ScrapedItem
from app.storage.local_s3 import LocalS3Storage
from app.workers.celery_app import celery
from app.workers.matching_tasks import run_keyword_matching # Import matching task

storage = LocalS3Storage()

@celery.task(name="batch.process", queue="default")
def process_batch(project_id: str, file_path: str) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.ensure_future(_process_batch_async(project_id, file_path))
    else:
        return asyncio.run(_process_batch_async(project_id, file_path))

async def _process_batch_async(project_id: str, file_path: str) -> dict:
    print(f"process_batch: running shared ingestion for file={file_path}")

    raw_data = storage.read_json(file_path)
    valid_items = []
    dead_letter_payload = []

    # 1. Validate incoming structures from Go Scraper / RSS feed
    for item_dict in raw_data:
        try:
            validated = ScrapedItem.model_validate(item_dict)
            valid_items.append(validated.model_dump())
        except Exception as exc:
            dead_letter_payload.append({"item": item_dict, "error": str(exc)})

    inserted_ids = []
    
    # 2. Bulk insert into the shared engineering layer (RawPost)
    if valid_items:
        async with SessionLocal() as db:
            # Call the ingestion service helper to populate raw_posts globally
            inserted_ids = await bulk_upsert_raw_posts(db, valid_items, source_run_id="rss_go_run")
            await db.commit()

    # 3. Fire-and-forget matching task using the generated raw post IDs
    if inserted_ids:
        # Pass strings of UUIDs to Celery matching task
        run_keyword_matching.delay([str(rid) for rid in inserted_ids], source_run_id="rss_go_run")

    if dead_letter_payload:
        storage.write_json(layer="dead-letter", mission_id=project_id, payload=dead_letter_payload)

    summary = {
        "project_id": project_id,
        "raw_posts_ingested": len(inserted_ids),
        "dead_letter": len(dead_letter_payload),
    }
    print(f"process_batch complete: {summary}")
    return summary