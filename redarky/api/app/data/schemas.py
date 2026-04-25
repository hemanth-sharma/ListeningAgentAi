from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class RawItemSchema(BaseModel):
    source: str
    external_id: str
    title: str
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    score: Optional[int] = 0
    scraped_at: datetime