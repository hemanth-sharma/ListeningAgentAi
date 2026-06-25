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
    """Generates a stable unique SHA-256 string for content deduplication."""
    hasher = hashlib.sha256()
    hasher.update(item.source.encode('utf-8'))
    hasher.update(item.external_id.encode('utf-8'))
    return hasher.hexdigest()

@celery.task
def process_batch(project_id: str, file_path: str):
    """
    Safely wrappers execution across both eager testing environments
    and standard decoupled production background worker instances.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.ensure_future(_process_batch_async(project_id, file_path))
    else:
        return asyncio.run(_process_batch_async(project_id, file_path))

async def _process_batch_async(project_id: str, file_path: str) -> None:
    print(f"Processing batch file for project {project_id}: {file_path}")
    
    raw_data = storage.read_json(file_path)
    processed_payload = []
    dead_letter_payload = []
    
    inserted_count = 0
    skipped_count = 0

    async with SessionLocal() as db:
        for item in raw_data:
            try:
                # Structural safety check against your shared app/scraper/schemas schema
                validated = ScrapedItem.model_validate(item)
                
                # Check for item uniqueness using Redis Sets distributed lock setup
                hash_key = generate_post_hash(validated)
                if is_duplicate(project_id, hash_key):
                    skipped_count += 1
                    continue

                # Prepare the insert values mapping to your core app.posts.models table setup
                # Ensuring structural mapping fields align perfectly
                stmt = (
                    insert(Post)
                    .values(
                        project_id=UUID(project_id),
                        source=validated.source,
                        external_id=validated.external_id,
                        title=validated.title,
                        content=validated.content,
                        url=validated.url,
                        author=validated.author,
                        score=validated.score or 0,
                        scraped_at=validated.scraped_at,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    # Enforces idempotent database saves using unique composite indexes
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
                dead_letter_payload.append({"item": item, "error": str(exc)})
                print(f"Failed to process element. Error: {exc}")

        # Flush transaction batch updates down to your database engine 
        await db.commit()

    # Log operational visibility metrics down to your configured local S3 layout
    if processed_payload:
        storage.write_json(layer="processed", mission_id=project_id, payload=processed_payload)
    if dead_letter_payload:
        storage.write_json(layer="dead-letter", mission_id=project_id, payload=dead_letter_payload)

    print(f"Batch completed for project {project_id}. Saved: {inserted_count}, Skipped/Dupes: {skipped_count}")

