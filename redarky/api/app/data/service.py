import hashlib
from app.data.schemas import RawItemSchema
from app.data.models import DataItem


def generate_hash(item: RawItemSchema):
    base = f"{item.url}_{item.title}"
    return hashlib.sha256(base.encode()).hexdigest()


def clean_text(text: str | None):
    if not text:
        return ""
    return text.strip()


def classify_item(item: RawItemSchema):
    # TEMP (later replace with LLM)
    if "?" in item.title:
        return "question", 0.0
    return "general", 0.0


def transform_to_model(item: RawItemSchema, mission_id):
    classification, sentiment = classify_item(item)

    return DataItem(
        mission_id=mission_id,
        source=item.source,
        external_id=item.external_id,
        title=item.title,
        content=clean_text(item.content),
        url=item.url,
        author=item.author,
        score=item.score,
        classification=classification,
        sentiment_score=sentiment,
        scraped_at=item.scraped_at,
    )