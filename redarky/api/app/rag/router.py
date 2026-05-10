"""
rag/router.py  —  FastAPI endpoints for RAG search
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.database import get_db
from app.rag.service import RetrievedDoc, get_context_for_query, search_similar
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    mission_id: Optional[str] = None
    top_k: int = 5


class SearchResponse(BaseModel):
    query: str
    results: list[dict]
    context: str


@router.post("/search", response_model=SearchResponse)
async def rag_search(payload: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Perform semantic similarity search over embedded data items.
    Returns top-k results plus a pre-formatted context string for LLM use.
    """
    docs: list[RetrievedDoc] = await search_similar(
        query=payload.query,
        db=db,
        mission_id=payload.mission_id,
        top_k=payload.top_k,
    )
    context = await get_context_for_query(
        query=payload.query,
        db=db,
        mission_id=payload.mission_id,
        top_k=payload.top_k,
    )
    return SearchResponse(
        query=payload.query,
        results=[doc.to_dict() for doc in docs],
        context=context,
    )
