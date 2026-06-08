from agents.graphs.mission_graph import graph

from agents.services.retrieval_service import semantic_search
from agents.services.agent_storage_service import save_agent_report


def run_agent_pipeline(
    mission_id: str,
    query: str,
):

    chunks = semantic_search(
        query=query,
        mission_id=mission_id,
        limit=10,
    )

    result = graph.invoke({
        "mission_id": mission_id,
        "query": query,
        "retrieved_chunks": chunks,
        "gaps": [],
        "specifications": [],
        "final_report": "",
        "current_agent": "",
        "status": "running",
        "errors": [],
    })

    save_agent_report(
        mission_id=mission_id,
        report=result["final_report"],
    )

    return result