import json
from sqlalchemy.orm import Session
from app.workers.celery_app import celery

from app.database import SessionLocal
from app.data.schemas import RawItemSchema
from app.data.service import generate_hash, transform_to_model
from app.utils.redis_client import is_duplicate


@celery.task(name="app.workers.tasks.process_batch")
def process_batch(mission_id: str, file_path: str):
    print(f"Processing batch: {file_path}")

    db: Session = SessionLocal()

    with open(file_path, "r") as f:
        raw_data = json.load(f)

    processed_count = 0
    skipped = 0

    for item in raw_data:
        try:
            validated = RawItemSchema(**item)

            # Dedup
            hash_key = generate_hash(validated)
            if is_duplicate(mission_id, hash_key):
                skipped += 1
                continue

            db_item = transform_to_model(validated, mission_id)
            db.add(db_item)

            processed_count += 1

        except Exception as e:
            print("Error processing item:", e)
            continue

    db.commit()
    db.close()

    print(f"Inserted: {processed_count}, Skipped: {skipped}")