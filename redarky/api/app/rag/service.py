"""
rag/service.py  —  MYM-46, 47
================================
Retrieval-Augmented Generation (RAG) service.

Provides:
  - search_similar(query, mission_id, top_k) → list[RetrievedDoc]
    Uses pgvector cosine similarity search via SQLAlchemy + asyncpg.

  - get_context_for_query(query, mission_id) → str
    Convenience wrapper that formats retrieved docs into an LLM-ready string.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

import openai
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.models import DataItem, Embedding

log = structlog.get_logger("rag.service")


# ──────────────────────────────────────────────────────────────
# Schema for search results
# ──────────────────────────────────────────────────────────────

class RetrievedDoc:
    """Lightweight dataclass for a retrieved document."""

    def __init__(
        self,
        data_item_id: str,
        title: str | None,
        content: str | None,
        url: str,
        source: str,
        similarity: float,
    ) -> None:
        self.data_item_id = data_item_id
        self.title = title
        self.content = content
        self.url = url
        self.source = source
        self.similarity = similarity

    def to_dict(self) -> dict:
        return {
            "data_item_id": self.data_item_id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "similarity": self.similarity,
        }

    def __repr__(self) -> str:
        return f"<RetrievedDoc id={self.data_item_id} sim={self.similarity:.4f}>"


# ──────────────────────────────────────────────────────────────
# Embedding helper
# ──────────────────────────────────────────────────────────────

def _get_openai_client() -> openai.AsyncOpenAI:
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in settings.")
    return openai.AsyncOpenAI(api_key=api_key)


async def embed_query(query: str) -> list[float]:
    """
    Embed a search query using OpenAI text-embedding-3-small.
    Returns a 1536-dimensional float vector.
    """
    client = _get_openai_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=query.strip()[:8000],
    )
    vector = response.data[0].embedding
    log.debug("embed_query.done", query_len=len(query), vector_dim=len(vector))
    return vector


# ──────────────────────────────────────────────────────────────
# Core search function  (MYM-46, 47)
# ──────────────────────────────────────────────────────────────

async def search_similar(
    query: str,
    db: AsyncSession,
    mission_id: Optional[str | UUID] = None,
    top_k: int = 5,
) -> list[RetrievedDoc]:
    """
    Find top-k data items most similar to `query` using pgvector cosine similarity.

    Args:
        query:      Natural language query string.
        db:         Async SQLAlchemy session (injected via FastAPI Depends).
        mission_id: Optional UUID to scope results to a specific mission.
        top_k:      Number of results to return (default 5).

    Returns:
        List of RetrievedDoc sorted by descending similarity.
    """
    log.info("search_similar.start", query=query, mission_id=str(mission_id), top_k=top_k)

    # 1. Embed the query
    query_vector: list[float] = await embed_query(query)

    # 2. Build pgvector cosine similarity query
    #    1 - (embedding <=> query_vector) gives cosine similarity (0→1)
    #    We use raw text() for the vector literal so it works with asyncpg
    vector_literal = "[" + ",".join(map(str, query_vector)) + "]"

    if mission_id:
        sql = text("""
            SELECT
                di.id,
                di.title,
                di.content,
                di.url,
                di.source,
                1 - (e.vector <=> :query_vec ::vector) AS similarity
            FROM embeddings e
            JOIN data_items di ON di.id = e.data_item_id
            WHERE di.mission_id = :mission_id
              AND e.vector IS NOT NULL
            ORDER BY e.vector <=> :query_vec ::vector
            LIMIT :top_k
        """)
        result = await db.execute(
            sql,
            {
                "query_vec": vector_literal,
                "mission_id": str(mission_id),
                "top_k": top_k,
            },
        )
    else:
        sql = text("""
            SELECT
                di.id,
                di.title,
                di.content,
                di.url,
                di.source,
                1 - (e.vector <=> :query_vec ::vector) AS similarity
            FROM embeddings e
            JOIN data_items di ON di.id = e.data_item_id
            WHERE e.vector IS NOT NULL
            ORDER BY e.vector <=> :query_vec ::vector
            LIMIT :top_k
        """)
        result = await db.execute(sql, {"query_vec": vector_literal, "top_k": top_k})

    rows = result.fetchall()
    docs = [
        RetrievedDoc(
            data_item_id=str(row[0]),
            title=row[1],
            content=row[2],
            url=row[3],
            source=row[4],
            similarity=float(row[5]),
        )
        for row in rows
    ]

    log.info("search_similar.done", results=len(docs))
    return docs


async def get_context_for_query(
    query: str,
    db: AsyncSession,
    mission_id: Optional[str | UUID] = None,
    top_k: int = 5,
    max_chars_per_doc: int = 800,
) -> str:
    """
    Retrieve top-k similar docs and format them as a context string
    suitable for injection into an LLM prompt.
    """
    docs = await search_similar(query=query, db=db, mission_id=mission_id, top_k=top_k)

    if not docs:
        return "No relevant context found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        snippet = (doc.content or doc.title or "")[:max_chars_per_doc]
        parts.append(
            f"[{i}] Source: {doc.source} | URL: {doc.url}\n"
            f"Title: {doc.title or 'N/A'}\n"
            f"Content: {snippet}\n"
            f"Similarity: {doc.similarity:.4f}"
        )

    return "\n\n---\n\n".join(parts)
