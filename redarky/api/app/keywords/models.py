"""
app/keywords/models.py

Added BRAND keyword type alongside existing INCLUDE / EXCLUDE.

Brand keywords work exactly like include keywords in terms of scraping,
but are tagged is_brand_mention=True on the resulting Post/Lead records.
This lets the frontend show a "Brand mention" badge separately from
"Intent lead" results.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class KeywordType(str, enum.Enum):
    INCLUDE = "include"   # trigger scraping, not a brand mention
    EXCLUDE = "exclude"   # filter out posts containing these (client-side)
    BRAND   = "brand"     # like include, but tagged is_brand_mention=True


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    keyword_type: Mapped[KeywordType] = mapped_column(
        SAEnum(KeywordType, name="keyword_type_enum"), nullable=False, default=KeywordType.INCLUDE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="keywords")