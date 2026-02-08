from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.db.fetch_thread_snapshot import fetch_thread_snapshot
from app.db.get_conn_factory import conn_factory
from app.db.run_repository import create_run
from app.db.thread_repository import ensure_thread
from .models import ApprovalDecision, ChatRequest
from .service import (
    build_initial_chat_state,
    ensure_thread_documents,
    graph_event_stream,
    persist_user_chat_message,
)
from .streaming import STREAM_RESPONSE_HEADERS

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/{thread_id}")
async def api_chat(thread_id: str, payload: ChatRequest):
    run_id = str(uuid.uuid4())

    ensure_thread(thread_id)
    create_run(run_id=run_id, thread_id=thread_id, trigger="chat", status="queued")

    user_message = persist_user_chat_message(thread_id, payload.message, run_id=run_id)
    ensure_thread_documents(thread_id)

    state_update = build_initial_chat_state(
        thread_id=thread_id,
        run_id=run_id,
        user_message=user_message,
    )

    return StreamingResponse(
        graph_event_stream(
            thread_id=thread_id,
            run_id=run_id,
            graph_input=state_update,
            trigger="chat",
        ),
        media_type="text/event-stream",
        headers=STREAM_RESPONSE_HEADERS,
    )


@router.get("/chat/{thread_id}")
async def get_chat_snapshot(thread_id: str):
    with conn_factory() as conn:
        snapshot = fetch_thread_snapshot(conn, thread_id)

    return {
        "ok": True,
        "thread_id": thread_id,
        **snapshot,
    }


@router.post("/chat/{thread_id}/approval")
async def approve_changeset(thread_id: str, payload: ApprovalDecision):
    run_id = str(uuid.uuid4())

    ensure_thread(thread_id)
    create_run(run_id=run_id, thread_id=thread_id, trigger="approval", status="queued")

    resume_payload = {"decision": payload.decision}
    if payload.comment:
        resume_payload["comment"] = payload.comment

    resume_value: dict[str, object] | object = resume_payload
    if payload.interrupt_id:
        resume_value = {payload.interrupt_id: resume_payload}

    resume = Command(resume=resume_value, update={"run_id": run_id})

    return StreamingResponse(
        graph_event_stream(
            thread_id=thread_id,
            run_id=run_id,
            graph_input=resume,
            trigger="approval",
        ),
        media_type="text/event-stream",
        headers=STREAM_RESPONSE_HEADERS,
    )
