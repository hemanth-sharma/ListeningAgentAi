"""
agents/state/agent_state.py  —  MYM-48
=======================================
Pydantic-based AgentState definition for the LangGraph mission graph.

This is the single shared state object that flows through every node
in the supervisor → researcher pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


from typing import TypedDict, List, Dict, Optional


class AgentState(TypedDict):
    mission_id: str
    query: str

    retrieved_chunks: List[Dict]

    gaps: List[str]

    specifications: List[Dict]

    final_report: str

    current_agent: str

    status: str

    errors: List[str]



# class RetrievedDoc(BaseModel):
#     """A single document retrieved from the pgvector similarity search."""

#     data_item_id: str
#     title: Optional[str] = None
#     content: Optional[str] = None
#     url: str
#     source: str
#     similarity: float = 0.0


# class ResearchOutput(BaseModel):
#     """Structured output produced by the researcher node."""

#     summary: str = ""
#     key_themes: list[str] = Field(default_factory=list)
#     sentiment: str = "neutral"  # positive | neutral | negative
#     raw: dict[str, Any] = Field(default_factory=dict)


# class AnalysisOutput(BaseModel):
#     """Structured output produced by the supervisor / analysis node."""

#     market_gaps: list[dict[str, Any]] = Field(default_factory=list)
#     recommendations: list[str] = Field(default_factory=list)
#     confidence: float = 0.0
#     raw: dict[str, Any] = Field(default_factory=dict)


# class AgentState(BaseModel):
#     """
#     The canonical state object passed between all LangGraph nodes.

#     Fields:
#         mission_id      — UUID of the mission being analysed.
#         query           — The natural-language query driving the research.
#         retrieved_docs  — Documents retrieved from the RAG layer.
#         research        — Output from the researcher node.
#         analysis        — Output from the supervisor / analysis node.
#         error           — Set if any node encounters a fatal error.
#         metadata        — Arbitrary key-value bag for inter-node communication.
#         created_at      — Timestamp when the state was initialised.
#         run_id          — Unique ID for this graph execution.
#     """

#     run_id: str = Field(default_factory=lambda: str(uuid4()))
#     mission_id: str
#     query: str = ""

#     # RAG layer output
#     retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)

#     # Node outputs
#     research: Optional[ResearchOutput] = None
#     analysis: Optional[AnalysisOutput] = None

#     # Control flow
#     error: Optional[str] = None
#     next_node: Optional[str] = None   # supervisor uses this to route

#     # Arbitrary metadata
#     metadata: dict[str, Any] = Field(default_factory=dict)

#     created_at: str = Field(
#         default_factory=lambda: datetime.now(timezone.utc).isoformat()
#     )

#     class Config:
#         arbitrary_types_allowed = True
