"""
agents/nodes/supervisor_node.py  —  MYM-49
============================================
Supervisor node: orchestrates the research pipeline.

Responsibilities:
  1. Decide which node to call next based on current state.
  2. After researcher finishes, synthesise a final analysis.
  3. Set state.next_node to route the graph.

This is a skeleton implementation — logic stubs are marked with TODO.
"""

from __future__ import annotations

import structlog

from redarky.agents.state.agent_state import AgentState, AnalysisOutput

log = structlog.get_logger("agents.supervisor")


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node function.

    Called at two points in the graph:
      1. Start → decides to route to 'researcher'
      2. After researcher → synthesises analysis and ends graph

    Returns updated AgentState.
    """
    log.info(
        "supervisor_node.enter",
        run_id=state.run_id,
        mission_id=state.mission_id,
        has_research=state.research is not None,
    )

    try:
        if state.error:
            # Propagate error — don't attempt analysis
            log.warning("supervisor_node.error_state", error=state.error)
            state = state.model_copy(update={"next_node": "__end__"})
            return state

        if state.research is None:
            # First pass: route to researcher
            log.info("supervisor_node.routing_to_researcher", run_id=state.run_id)
            state = state.model_copy(update={"next_node": "researcher"})
            return state

        # Second pass: researcher has returned results — synthesise
        log.info("supervisor_node.synthesising", run_id=state.run_id)

        # TODO (Phase 3): Replace with real LLM call using retrieved_docs + research output
        analysis = AnalysisOutput(
            market_gaps=[
                {
                    "title": f"Gap identified from: {state.query}",
                    "description": "TODO: LLM-generated gap description",
                    "confidence": 0.5,
                    "evidence": [doc.url for doc in state.retrieved_docs[:3]],
                }
            ],
            recommendations=[
                "TODO: Add real recommendations from LLM analysis"
            ],
            confidence=0.5,
            raw={
                "research_summary": state.research.summary if state.research else "",
                "doc_count": len(state.retrieved_docs),
            },
        )

        state = state.model_copy(update={"analysis": analysis, "next_node": "__end__"})

    except Exception as exc:
        log.exception("supervisor_node.failed", run_id=state.run_id, error=str(exc))
        state = state.model_copy(update={"error": str(exc), "next_node": "__end__"})

    return state
