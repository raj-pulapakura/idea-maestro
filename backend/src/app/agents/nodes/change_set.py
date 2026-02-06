from __future__ import annotations

from datetime import datetime, timezone
from difflib import unified_diff
import uuid

from langgraph.types import Command, interrupt

from app.agents.helpers.emit_event import emit_event
from app.agents.state.types import AgentState, ChangeSet, StagedEdit, Doc
from app.db.get_conn_factory import conn_factory
from app.db.persist_docs_to_db import persist_docs_to_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_changeset_node(state: AgentState) -> dict:
    edits = state.get("staged_edits", [])
    if not edits:
        return {}

    latest_by_doc: dict[str, str] = {}
    for edit in edits:
        latest_by_doc[edit["doc_id"]] = edit["new_content"]

    diffs: dict[str, str] = {}
    finalized_edits: list[StagedEdit] = []

    for doc_id, new_content in latest_by_doc.items():
        old_content = state.get("docs", {}).get(doc_id, {}).get("content", "")
        diff = "".join(
            unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{doc_id}",
                tofile=f"b/{doc_id}",
            )
        )
        diffs[doc_id] = diff
        finalized_edits.append({"doc_id": doc_id, "new_content": new_content})

    cs_id = str(uuid.uuid4())
    created_by = state.get("staged_edits_by") or "agent"
    changeset: ChangeSet = {
        "change_set_id": cs_id,
        "created_by": created_by,
        "created_at": _now_iso(),
        "summary": state.get("staged_edits_summary", ""),
        "edits": finalized_edits,
        "diffs": diffs,
        "status": "pending",
    }

    emit_event(
        "changeset.created",
        {
            "change_set_id": cs_id,
            "created_by": created_by,
            "docs": list(latest_by_doc.keys()),
            "summary": changeset["summary"],
        },
    )

    return {
        "pending_change_set": changeset,
        "staged_edits": [],
        "staged_edits_summary": "",
        "staged_edits_by": "",
    }


def await_approval_node(state: AgentState):
    cs = state.get("pending_change_set")
    if not cs or cs.get("status") != "pending":
        return {}

    decision = interrupt(
        {
            "type": "approval_required",
            "change_set": {
                "change_set_id": cs["change_set_id"],
                "summary": cs["summary"],
                "diffs": cs["diffs"],
                "docs": [e["doc_id"] for e in cs["edits"]],
            },
        }
    )

    if isinstance(decision, dict) and decision.get("decision") == "approve":
        emit_event("changeset.approved", {"change_set_id": cs["change_set_id"]})
        return Command(goto="apply_changeset")

    emit_event("changeset.rejected", {"change_set_id": cs["change_set_id"]})
    return Command(goto="reject_changeset")


def apply_changeset_node(state: AgentState) -> dict:
    cs = state.get("pending_change_set")
    if not cs:
        return {}

    updates: dict[str, Doc] = {}
    docs = state.get("docs", {})
    for edit in cs["staged_edits"]:
        doc_id = edit["doc_id"]
        old = docs.get(doc_id)
        if not old:
            continue

        new_doc = dict(old)
        new_doc["content"] = edit["new_content"]
        new_doc["description"] = cs.get("staged_edits_summary", "")
        new_doc["updated_by"] = cs.get("created_by", "agent")
        new_doc["updated_at"] = _now_iso()
        updates[doc_id] = new_doc

    thread_id = state.get("thread_id")
    if not thread_id:
        raise ValueError("thread_id is required")

    persist_docs_to_db(conn_factory(), thread_id, updates)

    emit_event(
        "changeset.applied",
        {
            "change_set_id": cs["change_set_id"],
            "docs": list(updates.keys()),
        },
    )

    merged_docs = dict(docs)
    merged_docs.update(updates)

    return {
        "docs": merged_docs,
        "pending_change_set": None,
    }


def reject_changeset_node(state: AgentState) -> dict:
    cs = state.get("pending_change_set")
    if cs:
        emit_event("changeset.discarded", {"change_set_id": cs["change_set_id"]})
    return {"pending_change_set": None}
