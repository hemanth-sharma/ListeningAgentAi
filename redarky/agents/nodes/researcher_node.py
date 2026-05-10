"""
agents/nodes/researcher_node.py  —  MYM-49
============================================
Researcher node: consumes retrieved_docs and produces ResearchOutput.

This is a skeleton implementation — logic stubs are marked with TODO.
In Phase 3, this will be replaced with a real LangChain/LLM call.
"""

from __future__ import annotations

import structlog

from agents.state.agent_state import AgentState, ResearchOutput

log = structlog.get_logger("agents.researcher")


def researcher_node(state: AgentState) -> AgentState:
    """
    Researcher node function.

    Takes the retrieved_docs from RAG and produces a structured ResearchOutput.
    The supervisor node routes here and then returns control to the supervisor.

    Returns updated AgentState with research field populated.
    """
    log.info(
        "researcher_node.enter",
        run_id=state.run_id,
        mission_id=state.mission_id,
        doc_count=len(state.retrieved_docs),
    )

    try:
        # TODO (Phase 3): Replace with real LLM call
        # Example:
        #   llm = ChatOpenAI(model="gpt-4o-mini")
        #   chain = researcher_prompt | llm | StrOutputParser()
        #   summary = await chain.ainvoke({"docs": state.retrieved_docs, "query": state.query})

        # Skeleton: extract top titles and sources as "research"
        themes = list({doc.source for doc in state.retrieved_docs})
        top_titles = [doc.title for doc in state.retrieved_docs[:5] if doc.title]

        research = ResearchOutput(
            summary=(
                f"Researched {len(state.retrieved_docs)} documents for query: '{state.query}'. "
                f"Top sources: {', '.join(themes[:3])}. "
                f"TODO: Replace with LLM-generated summary."
            ),
            key_themes=themes,
            sentiment="neutral",  # TODO: sentiment analysis
            raw={
                "top_titles": top_titles,
                "doc_count": len(state.retrieved_docs),
                "query": state.query,
            },
        )

        # Route back to supervisor for synthesis
        state = state.model_copy(
            update={"research": research, "next_node": "supervisor"}
        )

    except Exception as exc:
        log.exception("researcher_node.failed", run_id=state.run_id, error=str(exc))
        state = state.model_copy(update={"error": str(exc), "next_node": "__end__"})

    log.info(
        "researcher_node.done",
        run_id=state.run_id,
        themes=state.research.key_themes if state.research else [],
    )

    return state
