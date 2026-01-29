from dataclasses import dataclass
from fastapi import APIRouter, Request

from typing import TypedDict
from langchain_core.messages import AIMessageChunk
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver
from langgraph.types import Command, interrupt
import os

from app.agents.main import build_workflow

model = init_chat_model(model="gpt-4o-mini", temperature=0.0)

config = {"configurable": {"thread_id": 1}}


class State(TypedDict):
    document: str
    suggested_edit: str

def suggest_edit(state: State) -> State:
    response = model.invoke(f"Expand on the following document. Overwrite: {state['document']}")
    return {"suggested_edit": response.content}

def approve_edit(state: State) -> State:
    approved = interrupt({
        "question": "Do you approve of this edit?",
        "details": state["suggested_edit"],
    })

    if approved:
        print("edit approved")
        return Command(goto="make_edit")
    else:
        return Command(goto="cancel")

def make_edit(state: State) -> State:
    print("edit made")
    return {"document": state["suggested_edit"]}

def cancel(state: State) -> State:
    return {"document": state["document"]}

DB_URL = os.getenv("DATABASE_URL") + "?sslmode=disable"
print(DB_URL)



router = APIRouter(prefix="/api", tags=["test"])


def checkpointer_decorator(func):
    """
    Decorator that opens a PostgresSaver context for the duration of the request
    and attaches it to request.state.checkpointer.

    Note: The wrapper intentionally only accepts `request: Request` so FastAPI
    does not interpret extra *args/**kwargs as query parameters.
    """

    async def wrapper(request: Request):
        with PostgresSaver.from_conn_string(DB_URL) as checkpointer:
            checkpointer.setup()
            request.state.checkpointer = checkpointer
            return await func(request)

    return wrapper




@router.get("/test")
@checkpointer_decorator
async def api_test(request: Request):
    checkpointer = getattr(request.state, "checkpointer", None)

    workflow = build_workflow()
    graph = workflow.compile(checkpointer=checkpointer)

    is_thinking = False

    for mode, chunk in graph.stream(
        {"user_query": "I want to build a meme cat app"},
        stream_mode=["messages", "updates"],
        config=config,
    ):
        if mode == "messages":
            msg, _ = chunk
            msg: AIMessageChunk = msg
            if len(msg.content) == 0: continue

            type = msg.content[0]["type"]

            if type == "thinking" and "thinking" in msg.content[0]:
                if not is_thinking:
                    is_thinking = True
                    print("Thinking: ", end="")
                text = msg.content[0]["thinking"]
                print(text, end="")
            elif type == "text" and "text" in msg.content[0]:
                if is_thinking:
                    is_thinking = False
                    print("\n Response: ", end="")
                text = msg.content[0]["text"]
                print(text, end="")

        elif mode == "updates":
            if "__interrupt__" in chunk:
                print("\ninterrupted, breaking. waiting for user approval.")
                break
            else:
                # print("state update: ", chunk)
                pass

    return {"ok": True, "route": "/api/test", "state": ""}


@router.post("/approve")
@checkpointer_decorator
async def approve(request: Request):
    # Use the PostgresSaver context attached by the decorator
    checkpointer = getattr(request.state, "checkpointer", None)

    workflow = build_workflow()
    graph = workflow.compile(checkpointer=checkpointer)

    async for mode, chunk in graph.astream(
        Command(resume=True),
        stream_mode=["messages", "updates"],
        config=config,
    ):
        if mode == "messages":
            msg, _ = chunk
            if isinstance(msg, AIMessageChunk) and msg.content:
                print(msg.content, end="")

        elif mode == "updates":
            print("state update: ", chunk)

    return {"ok": True, "route": "/api/approve", "state": ""}
