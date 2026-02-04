from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
import uuid
from app.agents.main import build_workflow
from app.db.URL import DB_URL
from app.db.persist_messages_to_db import persist_messages_to_db
from app.db.get_conn_factory import conn_factory
from app.db.lc_message_to_row import lc_message_to_row
from app.db.fetch_thread_messages import fetch_thread_messages
from app.agents.state.get_initial_state_update import get_initial_state_update

router = APIRouter(prefix="/api", tags=["chat"])

class ApprovalDecision(BaseModel):
    decision: str = Field(description="approve or reject")


@router.post("/chat/{thread_id}")
async def api_chat(request: Request, thread_id: str):

    # TODO: this is a temporary solution to get a thread id for the chat
    thread_id = str(uuid.uuid4())
    # TODO: need to do a db call to check if the thread id is new
    is_new_thread = True

    with PostgresSaver.from_conn_string(DB_URL+"?sslmode=disable") as checkpointer:

        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        user_message = HumanMessage(content="I want to build a meme cat app")

        persist_messages_to_db(conn_factory(), thread_id, [lc_message_to_row(user_message)])

        state_update = get_initial_state_update(is_new_thread, thread_id, user_message)

        for namespace, mode, data in graph.stream(
            state_update,
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True
        ):
            if mode == "messages":
                msg, _ = data
                msg: AIMessageChunk = msg
                # print(msg)

            elif mode == "custom":
                # print("event: ", data)
                pass

            elif mode == "updates":
                print(f"\n stream update (namespace: {namespace}, mode: {mode})")
                print(data)
                if "__interrupt__" in data:
                    print("\ninterrupted, breaking. waiting for user approval.")
                    break

        return {"ok": True, "route": f"/api/chat/{thread_id}", "state": ""}


@router.get("/chat/{thread_id}")
async def get_chat_messages(thread_id: str):
    """Fetch all messages for a given thread."""
    with conn_factory() as conn:
        messages = fetch_thread_messages(conn, thread_id)
        return {"ok": True, "thread_id": thread_id, "messages": messages}


@router.post("/chat/{thread_id}/approval")
async def approve_changeset(thread_id: str, payload: ApprovalDecision):
    with PostgresSaver.from_conn_string(DB_URL + "?sslmode=disable") as checkpointer:
        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        print("\n\n\n\n")
        print(payload.decision)
        print("\n\n\n\n")

        for namespace, mode, data in graph.stream(
            Command(resume={"decision": payload.decision}),
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True,
        ):
            print(f"\n stream update (namespace: {namespace}, mode: {mode})")
            if mode == "messages":
                msg, _ = data
                msg: AIMessageChunk = msg
                print(msg)
            elif mode == "custom":
                print("event: ", data)
            elif mode == "updates":
                if "__interrupt__" in data:
                    print("\ninterrupted again, awaiting approval.")
                    break

    return {"ok": True, "thread_id": thread_id, "decision": payload.decision}


