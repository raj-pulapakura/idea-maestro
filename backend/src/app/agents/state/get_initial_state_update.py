from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agents.state.types import AgentState, Doc


def get_initial_state_update(
    *,
    thread_id: str,
    run_id: str,
    user_message: HumanMessage,
    docs: dict[str, Doc],
) -> AgentState:
    return {
        "thread_id": thread_id,
        "run_id": run_id,
        "next_agent": None,
        "messages": [user_message],
        "docs": docs,
        "docs_summary": {
            doc_id: (doc.get("description") or "no content yet")
            for doc_id, doc in docs.items()
        },
        "staged_edits": [],
        "staged_edits_summary": "",
        "staged_edits_by": "",
        "pending_change_set": None,
    }
