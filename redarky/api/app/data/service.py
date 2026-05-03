import hashlib
import uuid
from datetime import datetime, timezone # Added timezone
from app.data.schemas import RawItemSchema
from app.models import DataItem

def generate_hash(item: RawItemSchema) -> str:
    base = f"{item.source}|{item.external_id}|{item.url}|{item.title}"
    return hashlib.sha256(base.encode()).hexdigest()

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return text.strip()

def classify_item(item: RawItemSchema) -> tuple[str, float]:
    # TEMP (later replace with LLM)
    if item.title and "?" in item.title:
        return "question", 0.0
    return "general", 0.0

def transform_to_model(item: RawItemSchema, mission_id: str, dedup_hash: str) -> DataItem:
    classification, sentiment = classify_item(item)

    # 1. Ensure scraped_at is timezone-aware to match the new DB schema
    scraped_at = item.scraped_at
    if scraped_at.tzinfo is None:
        scraped_at = scraped_at.replace(tzinfo=timezone.utc)

    return DataItem(
        id=uuid.uuid4(),  # Manually set because Core Insert ignores model defaults
        mission_id=mission_id,
        source=item.source,
        external_id=item.external_id,
        dedup_hash=dedup_hash,
        title=item.title,
        content=clean_text(item.content),
        url=str(item.url),
        author=item.author,
        score=item.score,
        classification=classification,
        sentiment_score=sentiment,
        scraped_at=scraped_at,
        # 2. FIX: Manually set created_at because Core Insert ignores model defaults
        created_at=datetime.now(timezone.utc) 
    )