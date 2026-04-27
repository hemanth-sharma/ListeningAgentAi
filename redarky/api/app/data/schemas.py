from pydantic import BaseModel, ConfigDict, HttpUrl
from datetime import datetime


class RawItemSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str
    title: str
    content: str | None = None
    url: HttpUrl
    author: str | None = None
    score: int | None = 0
    scraped_at: datetime