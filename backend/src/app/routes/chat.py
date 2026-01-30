from fastapi import APIRouter, Request

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
import uuid
from app.agents.main import build_workflow
from app.db.URL import DB_URL
from app.db.persist_messages_to_db import persist_messages_to_db
from app.db.get_conn_factory import conn_factory
from app.db.lc_message_to_row import lc_message_to_row
from app.db.fetch_thread_messages import fetch_thread_messages

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/{thread_id}")
async def api_chat(request: Request, thread_id: str):

    # TODO: this is a temporary solution to get a thread id for the chat
    thread_id = str(uuid.uuid4())

    with PostgresSaver.from_conn_string(DB_URL+"?sslmode=disable") as checkpointer:

        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        user_message = HumanMessage(content="I want to build a meme cat app")

        persist_messages_to_db(conn_factory(), thread_id, [lc_message_to_row(user_message)])

        state_update = {
            "thread_id": thread_id,
            "messages": [user_message]
        }

        for mode, chunk in graph.stream(
            state_update,
            stream_mode=["messages", "updates"],
            config=config,
        ):
            if mode == "messages":
                msg, _ = chunk
                msg: AIMessageChunk = msg
                print(msg)

            elif mode == "updates":
                if "__interrupt__" in chunk:
                    print("\ninterrupted, breaking. waiting for user approval.")
                    break
                else:
                    # print("state update: ", chunk)
                    pass

        return {"ok": True, "route": f"/api/chat/{thread_id}", "state": ""}


@router.get("/chat/{thread_id}")
async def get_chat_messages(thread_id: str):
    """Fetch all messages for a given thread."""
    with conn_factory() as conn:
        messages = fetch_thread_messages(conn, thread_id)
        return {"ok": True, "thread_id": thread_id, "messages": messages}

