from __future__ import annotations

from typing import Annotated, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# --- Reducers ---

def append_history(old: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Accumulate history entries."""
    return (old or []) + (new or [])

def append_proposed_edits(
    old: list["ProposedEdit"] | None,
    new: list["ProposedEdit"] | None,
) -> list["ProposedEdit"]:
    return (old or []) + (new or [])

def merge_docs(
    old: dict[str, "Doc"] | None,
    new: dict[str, "Doc"] | None,
) -> dict[str, "Doc"]:
    """
    Merge docs by doc_id. New keys overwrite old keys; others preserved.
    """
    merged = dict(old or {})
    if new:
        merged.update(new)
    return merged

def merge_docs_mental_model(
    old: dict[str, str] | None,
    new: dict[str, str] | None,
) -> dict[str, str]:
    """
    Merge docs mental model by doc_id. New keys overwrite old keys; others preserved.
    """
    merged = dict(old or {})
    if new:
        merged.update(new)
    return merged

def set_pending_change_set(
    old: "ChangeSet | None",
    new: "ChangeSet | None",
) -> "ChangeSet | None":
    """
    'Last write wins' for pending_change_set.
    If a node returns None, it will clear it.
    """
    return new


# --- State ---

class Doc(TypedDict):
    title: str
    content: str
    description: str
    doc_type: str
    updated_by: str
    updated_at: str

class ProposedEdit(TypedDict):
    doc_id: str
    new_content: str

class ChangeSet(TypedDict):
    change_set_id: str
    created_by: str
    created_at: str
    edits: list[ProposedEdit]
    diffs: dict[str, str]
    summary: str
    status: str


class AgentState(TypedDict):
    thread_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    history: Annotated[list[Any], append_history]
    docs: Annotated[dict[str, Doc], merge_docs]
    docs_summary: Annotated[dict[str, str], merge_docs_mental_model] # summary of the docs for the agent to use in the prompt, so we don't load the entire prompt into memory
    proposed_edits: Annotated[list[ProposedEdit], append_proposed_edits]
    proposal_summary: str
    proposal_by: str
    pending_change_set: Annotated[ChangeSet | None, set_pending_change_set]
