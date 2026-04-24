# app/models.py (or missions/models.py)
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class ScrapedResult(Base):
    __tablename__ = "scraped_results"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    url = Column(String)
    query = Column(String) # To track which mission/search found this
    created_at = Column(DateTime(timezone=True), server_default=func.now())