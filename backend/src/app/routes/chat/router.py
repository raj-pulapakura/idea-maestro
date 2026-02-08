from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.db.fetch_thread_messages import fetch_thread_messages
from app.db.get_conn_factory import conn_factory
from .models import ApprovalDecision, ChatRequest
from .service import (
    build_initial_chat_state,
    ensure_thread_documents,
    graph_event_stream,
    persist_user_chat_message,
    thread_exists,
)
from .streaming import STREAM_RESPONSE_HEADERS

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/{thread_id}")
async def api_chat(thread_id: str, payload: ChatRequest):
    is_new_thread = not thread_exists(thread_id)
    user_message = persist_user_chat_message(thread_id, payload.message)
    ensure_thread_documents(thread_id, is_new_thread)

    state_update = build_initial_chat_state(
        thread_id=thread_id,
        is_new_thread=is_new_thread,
        user_message=user_message,
    )

    return StreamingResponse(
        graph_event_stream(
            thread_id=thread_id,
            graph_input=state_update,
            emit_thread_started=True,
        ),
        media_type="text/event-stream",
        headers=STREAM_RESPONSE_HEADERS,
    )


@router.get("/chat/{thread_id}")
async def get_chat_messages(thread_id: str):
    with conn_factory() as conn:
        messages = fetch_thread_messages(conn, thread_id)
        return {"ok": True, "thread_id": thread_id, "messages": messages}


@router.post("/chat/{thread_id}/approval")
async def approve_changeset(thread_id: str, payload: ApprovalDecision):
    return StreamingResponse(
        graph_event_stream(
            thread_id=thread_id,
            graph_input=Command(resume={"decision": payload.decision}),
            emit_thread_started=False,
        ),
        media_type="text/event-stream",
        headers=STREAM_RESPONSE_HEADERS,
    )
