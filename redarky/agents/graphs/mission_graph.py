"""
agents/graphs/mission_graph.py  —  MYM-48, 49
================================================
LangGraph StateGraph for the Mission Intelligence pipeline.

Graph structure:
  START
    ↓
  supervisor  ──(next_node == "researcher")──→  researcher
      ↑                                              │
      └─────────────────────────────────────────────┘
                  (next_node == "supervisor")
  supervisor  ──(next_node == "__end__")──→  END

The supervisor acts as both orchestrator and synthesiser.
This design mirrors a classic supervisor-researcher multi-agent pattern.
"""

from __future__ import annotations

from typing import Literal

import structlog
from langgraph.graph import END, START, StateGraph


from redarky.agents.nodes.researcher_node import researcher_node
from redarky.agents.nodes.supervisor_node import supervisor_node
from redarky.agents.state.agent_state import AgentState

log = structlog.get_logger("agents.mission_graph")


# ──────────────────────────────────────────────────────────────
# Routing function (edge condition)
# ──────────────────────────────────────────────────────────────

def route_from_supervisor(state: AgentState) -> Literal["researcher", "__end__"]:
    """
    Conditional edge from the supervisor node.
    The supervisor sets state.next_node to control routing.
    """
    destination = state.next_node or "__end__"
    log.debug("route_from_supervisor", run_id=state.run_id, destination=destination)
    return destination  


def route_from_researcher(state: AgentState) -> Literal["supervisor", "__end__"]:
    """
    Conditional edge from the researcher node.
    Normally routes back to supervisor for synthesis.
    If an error occurred, routes to END.
    """
    if state.error:
        return "__end__"
    destination = state.next_node or "supervisor"
    log.debug("route_from_researcher", run_id=state.run_id, destination=destination)
    return destination  # type: ignore[return-value]


# ──────────────────────────────────────────────────────────────
# Build the graph
# ──────────────────────────────────────────────────────────────

def build_mission_graph() -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph for mission intelligence.

    Returns a compiled graph ready to invoke with an AgentState.
    """
    # NOTE: LangGraph 0.1.x uses dict-based state; we wrap AgentState via .model_dump()
    # and rebuild via AgentState.model_validate() in the node wrappers.
    # This approach keeps nodes type-safe while remaining compatible with LangGraph.

    def _supervisor(state: dict) -> dict:
        agent_state = AgentState.model_validate(state)
        updated = supervisor_node(agent_state)
        return updated.model_dump()

    def _researcher(state: dict) -> dict:
        agent_state = AgentState.model_validate(state)
        updated = researcher_node(agent_state)
        return updated.model_dump()

    def _route_supervisor(state: dict) -> str:
        return route_from_supervisor(AgentState.model_validate(state))

    def _route_researcher(state: dict) -> str:
        return route_from_researcher(AgentState.model_validate(state))

    graph = StateGraph(dict)

    # Nodes
    graph.add_node("supervisor", _supervisor)
    graph.add_node("researcher", _researcher)

    # Edges
    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        _route_supervisor,
        {"researcher": "researcher", "__end__": END},
    )

    graph.add_conditional_edges(
        "researcher",
        _route_researcher,
        {"supervisor": "supervisor", "__end__": END},
    )

    compiled = graph.compile()
    log.info("mission_graph.compiled")
    return compiled


# Singleton compiled graph (import this in routers / tests)
mission_graph = build_mission_graph()


# ──────────────────────────────────────────────────────────────
# Public runner
# ──────────────────────────────────────────────────────────────

def run_mission_graph(
    mission_id: str,
    query: str,
    retrieved_docs: list[dict] | None = None,
) -> AgentState:
    """
    Convenience runner for the mission graph.

    Args:
        mission_id:     Mission UUID string.
        query:          Research query.
        retrieved_docs: Pre-fetched RAG docs (list of RetrievedDoc.to_dict()).

    Returns:
        Final AgentState after the graph completes.
    """
    initial_state = AgentState(
        mission_id=mission_id,
        query=query,
        retrieved_docs=retrieved_docs or [],
    )

    log.info(
        "run_mission_graph.start",
        run_id=initial_state.run_id,
        mission_id=mission_id,
        query=query,
        doc_count=len(initial_state.retrieved_docs),
    )

    result_dict = mission_graph.invoke(initial_state.model_dump())
    final_state = AgentState.model_validate(result_dict)

    log.info(
        "run_mission_graph.done",
        run_id=final_state.run_id,
        has_analysis=final_state.analysis is not None,
        error=final_state.error,
    )

    return final_state
