"""
instead of creating a static prompt based on the docs in app/agents/state/docs.py,
we create a function that builds a prompt based on the docs in the state,
as we assume that the agent may add docs to the state which are not in the static docs.py file.
"""

from app.agents.state.types import AgentState

def build_docs_summaries_prompt(state: AgentState) -> str:
    summaries = state.get("docs_summary") or {}
    prompt = ""
    for doc_id, summary in summaries.items():
        prompt += f"- {doc_id}: {summary}\n"
    return prompt