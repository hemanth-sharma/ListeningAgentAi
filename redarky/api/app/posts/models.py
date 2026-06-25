import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Changed to Optional/nullable since some posts can be title-only links
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Changed to Optional since some platforms mask authors
    url: Mapped[str] = mapped_column(Text, nullable=False) # Switched to Text as tracking URLs can easily exceed 255 chars
    
    score: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True) # Matches Celery insert format
    comments_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    created_at_platform: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Enforces native timezone-aware UTC dates standard
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="posts")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="post", cascade="all, delete-orphan")

    # Added Composite Constraint required for database-level .on_conflict_do_nothing() optimization
    __table_args__ = (
        UniqueConstraint("project_id", "external_id", name="uq_project_post_external_id"),
    )