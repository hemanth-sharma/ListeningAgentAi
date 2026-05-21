import json

from agents.state.agent_state import AgentState
from agents.prompts.spec_writer_prompt import SPEC_WRITER_PROMPT
from agents.services.llm_service import LLMService


llm = LLMService.get_openai()


def spec_writer_node(state: AgentState):

    chunks = state["retrieved_chunks"]

    content = "\n\n".join([
        x["content"][:2000]
        for x in chunks
    ])

    response = llm.invoke(
        f"{SPEC_WRITER_PROMPT}\n\n{content}"
    )

    try:
        state["specifications"] = json.loads(response.content)
    except Exception:
        state["specifications"] = []

    return state