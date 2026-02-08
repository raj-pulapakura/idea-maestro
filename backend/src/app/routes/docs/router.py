from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.fetch_thread_docs import fetch_thread_doc, fetch_thread_docs
from app.db.get_conn_factory import conn_factory

router = APIRouter(prefix="/api/threads/{thread_id}/docs", tags=["docs"])


def _serialize_doc(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "thread_id": row["thread_id"],
        "doc_id": row["doc_id"],
        "title": row["title"],
        "content": row["content"],
        "description": row["description"],
        "version": row["version"],
        "updated_by": row["updated_by"],
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


@router.get("")
async def api_list_docs(thread_id: str):
    with conn_factory() as conn:
        rows = fetch_thread_docs(conn, thread_id)

    return {
        "ok": True,
        "thread_id": thread_id,
        "docs": [_serialize_doc(row) for row in rows],
    }


@router.get("/{doc_id}")
async def api_get_doc(thread_id: str, doc_id: str):
    with conn_factory() as conn:
        row = fetch_thread_doc(conn, thread_id, doc_id)

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "ok": True,
        "thread_id": thread_id,
        "doc": _serialize_doc(row),
    }
