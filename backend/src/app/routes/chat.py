import json
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessageChunk, HumanMessage, BaseMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
import uuid
from app.agents.build_workflow import build_workflow
from app.db.URL import DB_URL
from app.db.persist_messages_to_db import persist_messages_to_db
from app.db.get_conn_factory import conn_factory
from app.db.lc_message_to_row import lc_message_to_row
from app.db.fetch_thread_messages import fetch_thread_messages
from app.agents.state.get_initial_state_update import get_initial_state_update
from app.agents.state.empty_docs import empty_docs
from app.db.persist_docs_to_db import persist_docs_to_db

router = APIRouter(prefix="/api", tags=["chat"])

class ApprovalDecision(BaseModel):
    decision: str = Field(description="approve or reject")


def make_json_serializable(obj):
    """Recursively convert objects to JSON-serializable format."""
    if isinstance(obj, BaseMessage):
        # Convert LangChain messages to dict
        return lc_message_to_row(obj)
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, BaseModel):
        # Handle Pydantic models
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        # Handle other objects with __dict__
        return make_json_serializable(obj.__dict__)
    else:
        # Try to return as-is if it's already serializable
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # Fallback: convert to string representation
            return str(obj)


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

        user_message = HumanMessage(content="""Problem: consultants want to practice their consulting skills in a non-pressured, self-paced environment, from the comfort of their own home.
Solution:
An app which simulates different consulting situations, from different fields (we can start with IT consulting, then move to different fields such as medical consulting etc.).
An AI coach will act as the client and the user (the consultant) will be put in a scenario in which they engage with the AI client.
The AI client will verbally talk, and the user will verbally respond.
Can simulate different scenarios, such as speaking with a difficult client, client language barriers, handling requirements scoping, and many different scenarios.
The user’s conversation and responses will be automatically graded, feedback will be given.
Principles:
Gamification: add streaks, badges, awards, XP. Take inspiration from Duolingo, one of the most successful learning platforms to ever exist.
Monetization:
I’m sure an app such as this will have tons of opportunities for a freemium based model (some features are available for free, other features have to paid for).
Can also have a separate package for enterprises ($10/per person). For enterprises that want to use ai consultant coach to offer their employees.
""")

        persist_messages_to_db(conn_factory(), thread_id, [lc_message_to_row(user_message)])

        if is_new_thread: 
            persist_docs_to_db(conn_factory(), thread_id, empty_docs)

        state_update = get_initial_state_update(is_new_thread, thread_id, user_message)

        for namespace, mode, data in graph.stream(
            state_update,
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True
        ):
            if mode == "messages":
                msg, _ = data
                # print(f"\n stream update (namespace: {namespace}, mode: {mode})")
                # print(json.dumps(make_json_serializable(msg), indent=4))

            elif mode == "custom":
                # print("event: ", data)
                pass

            elif mode == "updates":
                print(f"\n stream update (namespace: {namespace}, mode: {mode})")
                serializable_data = make_json_serializable(data)
                print(json.dumps(serializable_data, indent=4))
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

        for namespace, mode, data in graph.stream(
            Command(resume={"decision": payload.decision}),
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True,
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

    return {"ok": True, "thread_id": thread_id, "decision": payload.decision}


