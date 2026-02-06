
from langchain_core.messages import HumanMessage
from app.agents.state.types import AgentState
from app.agents.state.empty_docs import empty_docs


def get_initial_state_update(is_new_thread: bool, thread_id: str, user_message: HumanMessage) -> AgentState:
    state_update: AgentState = {
        "thread_id": thread_id,
        "messages": [user_message],
        "staged_edits": [],
        "staged_edits_summary": "",
        "staged_edits_by": "",
        "pending_change_set": None,
    }

    if is_new_thread:
        state_update["docs"] = empty_docs
        state_update["docs_summary"] = {doc_id: "no content yet" for doc_id in empty_docs.keys()}

    return state_update
