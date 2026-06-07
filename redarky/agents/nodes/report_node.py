from agents.state.agent_state import AgentState
from agents.prompts.report_prompt import REPORT_PROMPT
from agents.services.llm_service import LLMService


llm = LLMService.get_openai()


def report_node(state: AgentState):

    response = llm.invoke(
        f"""
        {REPORT_PROMPT}

        Retrieved Chunks:
        {state["retrieved_chunks"]}

        Gaps:
        {state["gaps"]}

        Specifications:
        {state["specifications"]}
        """
    )

    state["final_report"] = response.content

    return state