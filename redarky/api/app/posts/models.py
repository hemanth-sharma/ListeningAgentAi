"""
app/posts/models.py

Updated to store the new fields coming from the rewritten Go scraper:
  - post_type        ("post" | "comment")
  - subreddit        (populated for Reddit items)
  - matched_keyword  (which keyword triggered this hit)
  - is_brand_mention (True for brand keyword hits)
  - created_at_platform as an int (Unix timestamp from Go, not a string)
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Boolean, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Source identity ────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(String(64), nullable=False)         # "reddit" | "hn"
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)   # platform-native ID

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Engagement metrics ────────────────────────────────────────────────────
    score: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    comments_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # ── Classification (new) ─────────────────────────────────────────────────
    post_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # "post" | "comment" — comments are often higher-intent than top-level posts

    subreddit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Populated for Reddit items; empty string for HN

    matched_keyword: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # Stores which keyword from the user's keyword list triggered this scrape result.
    # Useful for the dashboard to show "Found via: 'need app developer'"

    is_brand_mention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True when the post was found via a BrandKeyword rather than an IncludeKeyword.
    # These are surfaced differently in the UI (brand monitoring feed vs. leads feed).

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at_platform: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # Unix timestamp of when the post was created on the platform.
    # Stored as BigInteger (not a string) for reliable date filtering.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project", back_populates="posts")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="post", cascade="all, delete-orphan")

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("project_id", "external_id", name="uq_project_post_external_id"),
    )