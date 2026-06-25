import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class LeadStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    CONTACTED = "contacted"
    CLOSED = "closed"
    IGNORED = "ignored"

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, native_enum=False, name="lead_status_enum"), 
        default=LeadStatus.NEW,
        nullable=False
    )
    
    buying_intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at_platform: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="leads")
    post: Mapped["Post"] = relationship("Post", back_populates="leads")

