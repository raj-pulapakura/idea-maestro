from __future__ import annotations

from typing import Annotated, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# --- Reducers ---

def append_history(old: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Accumulate history entries."""
    return (old or []) + (new or [])

def append_staged_edits(
    old: list["StagedEdit"] | None,
    new: list["StagedEdit"] | None,
) -> list["StagedEdit"]:
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

def set_staged_edits_summary(
    old: str | None,
    new: str | None,
) -> str | None:
    """
    'Last write wins' for staged_edits_summary.
    If a node returns None, it will clear it.
    """
    return new

def set_staged_edits_by(
    old: str | None,
    new: str | None,
) -> str | None:
    """
    'Last write wins' for staged_edits_by.
    If a node returns None, it will clear it.
    """
    return new

def set_next_agent(
    old: str | None,
    new: str | None,
) -> str | None:
    """
    'Last write wins' for next_agent.
    """
    return new


def set_int(
    old: int | None,
    new: int | None,
) -> int | None:
    return new


def set_loop_status(
    old: str | None,
    new: str | None,
) -> str | None:
    return new


def set_optional_text(
    old: str | None,
    new: str | None,
) -> str | None:
    return new


# --- State ---

class Doc(TypedDict):
    title: str
    content: str
    description: str
    version: int
    updated_by: str | None
    updated_at: str | None

class StagedEdit(TypedDict):
    doc_id: str
    new_content : str

class ChangeSet(TypedDict):
    change_set_id: str
    created_by: str
    created_at: str
    edits: list[StagedEdit]
    diffs: dict[str, str]
    summary: str
    status: str


class AgentState(TypedDict):
    thread_id: str
    run_id: str
    next_agent: Annotated[str | None, set_next_agent]
    messages: Annotated[list[BaseMessage], add_messages]
    history: Annotated[list[Any], append_history]
    docs: Annotated[dict[str, Doc], merge_docs]
    docs_summary: Annotated[dict[str, str], merge_docs_mental_model] # summary of the docs for the agent to use in the prompt, so we don't load the entire prompt into memory
    staged_edits: Annotated[list[StagedEdit], append_staged_edits]
    staged_edits_summary: Annotated[str | None, set_staged_edits_summary]
    staged_edits_by: Annotated[str | None, set_staged_edits_by]
    pending_change_set: Annotated[ChangeSet | None, set_pending_change_set]
    iteration_count: Annotated[int | None, set_int]
    max_iterations: Annotated[int | None, set_int]
    loop_status: Annotated[str | None, set_loop_status]
    last_routing_error: Annotated[str | None, set_optional_text]
    consecutive_noop_count: Annotated[int | None, set_int]
    last_supervisor_action: Annotated[str | None, set_optional_text]
    history_cursor_at_last_delegate: Annotated[int | None, set_int]
