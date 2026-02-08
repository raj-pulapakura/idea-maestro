from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.db.thread_repository import create_thread, list_threads, update_thread
from .models import CreateThreadRequest, UpdateThreadRequest

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _serialize_thread(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "thread_id": row["thread_id"],
        "title": row["title"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "last_message_preview": row["last_message_preview"],
    }


@router.get("")
async def api_list_threads(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    rows = list_threads(limit=limit, offset=offset)
    return {
        "ok": True,
        "threads": [_serialize_thread(row) for row in rows],
        "limit": limit,
        "offset": offset,
    }


@router.post("")
async def api_create_thread(payload: CreateThreadRequest):
    thread_id = payload.thread_id or str(uuid.uuid4())
    row = create_thread(thread_id=thread_id, title=payload.title, status=payload.status)
    return {
        "ok": True,
        "thread": _serialize_thread(row),
    }


@router.patch("/{thread_id}")
async def api_update_thread(thread_id: str, payload: UpdateThreadRequest):
    if payload.title is None and payload.status is None:
        raise HTTPException(status_code=400, detail="At least one field is required")

    row = update_thread(thread_id, title=payload.title, status=payload.status)
    if not row:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {
        "ok": True,
        "thread": _serialize_thread(row),
    }
