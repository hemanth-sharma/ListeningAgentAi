from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base


class DataItem(Base):
    __tablename__ = "data_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    mission_id = Column(UUID(as_uuid=True), nullable=False)

    source = Column(String)
    external_id = Column(String)

    title = Column(Text)
    content = Column(Text)
    url = Column(Text)

    author = Column(String)
    score = Column(Integer)

    classification = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)

    scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)