import json

from agents.state.agent_state import AgentState
from agents.prompts.gap_finder_prompt import GAP_FINDER_PROMPT
from agents.services.llm_service import LLMService


llm = LLMService.get_gemini()


def gap_finder_node(state: AgentState):

    chunks = state["retrieved_chunks"]

    content = "\n\n".join([
        x["content"][:2000]
        for x in chunks
    ])

    response = llm.invoke(
        f"{GAP_FINDER_PROMPT}\n\n{content}"
    )

    try:
        state["gaps"] = json.loads(response.content)
    except Exception:
        state["gaps"] = []

    return state