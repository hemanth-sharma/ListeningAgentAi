"""
api/app/agents/router.py
========================
FastAPI router to trigger the LangGraph mission intelligence pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# The agents/ package lives at redarky/agents/, one level above api/
# We add it to sys.path so the import works regardless of how the app is started.
_agents_root = str(Path(__file__).resolve().parents[4] / "agents")
if _agents_root not in sys.path:
    sys.path.insert(0, _agents_root)

router = APIRouter()


class AgentRunRequest(BaseModel):
    mission_id: str
    query: str
    retrieved_docs: Optional[list[dict[str, Any]]] = None


class AgentRunResponse(BaseModel):
    run_id: str
    mission_id: str
    query: str
    research: Optional[dict] = None
    analysis: Optional[dict] = None
    error: Optional[str] = None


@router.post("/run", response_model=AgentRunResponse)
def run_agent(payload: AgentRunRequest) -> AgentRunResponse:
    """
    Trigger the LangGraph supervisor-researcher pipeline for a mission.

    In Phase 3 this will be async and will call the RAG layer first.
    For now it accepts pre-fetched docs as an optional parameter.
    """
    try:
        # Lazy import keeps startup fast when langgraph is not installed
        from agents.graphs.mission_graph import run_mission_graph

        final_state = run_mission_graph(
            mission_id=payload.mission_id,
            query=payload.query,
            retrieved_docs=payload.retrieved_docs or [],
        )

        return AgentRunResponse(
            run_id=final_state.run_id,
            mission_id=final_state.mission_id,
            query=final_state.query,
            research=final_state.research.model_dump() if final_state.research else None,
            analysis=final_state.analysis.model_dump() if final_state.analysis else None,
            error=final_state.error,
        )

    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LangGraph not installed. Install langgraph>=0.1.0. Error: {exc}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
