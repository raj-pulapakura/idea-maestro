from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.changeset_repository import fetch_changeset_detail, fetch_changesets

router = APIRouter(prefix="/api/threads/{thread_id}/changesets", tags=["reviews"])


def _serialize_changeset(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_set_id": row["change_set_id"],
        "thread_id": row["thread_id"],
        "run_id": row["run_id"],
        "created_by": row["created_by"],
        "summary": row["summary"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "decided_at": row["decided_at"].isoformat() if row.get("decided_at") else None,
        "decision_note": row["decision_note"],
        "docs": row.get("docs", []),
        "diffs": row.get("diffs", {}),
    }


@router.get("")
async def api_list_changesets(thread_id: str):
    changesets = fetch_changesets(thread_id)
    return {
        "ok": True,
        "thread_id": thread_id,
        "changesets": [_serialize_changeset(changeset) for changeset in changesets],
    }


@router.get("/{change_set_id}")
async def api_get_changeset(thread_id: str, change_set_id: str):
    changeset = fetch_changeset_detail(thread_id, change_set_id)
    if not changeset:
        raise HTTPException(status_code=404, detail="Change set not found")

    serialized = _serialize_changeset(changeset)
    serialized["doc_changes"] = [
        {
            "doc_id": row["doc_id"],
            "before_content": row["before_content"],
            "after_content": row["after_content"],
            "diff": row["diff"],
        }
        for row in changeset.get("doc_changes", [])
    ]
    serialized["reviews"] = [
        {
            "decision": review["decision"],
            "comment": review["comment"],
            "reviewed_by": review["reviewed_by"],
            "reviewed_at": review["reviewed_at"].isoformat()
            if review.get("reviewed_at")
            else None,
        }
        for review in changeset.get("reviews", [])
    ]

    return {
        "ok": True,
        "thread_id": thread_id,
        "changeset": serialized,
    }
