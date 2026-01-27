from dataclasses import dataclass
from fastapi import APIRouter

from typing import TypedDict
from langchain_core.messages import AIMessageChunk
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver
from langgraph.types import Command, interrupt
import os

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



workflow = StateGraph(State)
workflow.add_node("suggest_edit", suggest_edit)
workflow.add_node("approve_edit", approve_edit)
workflow.add_node("make_edit", make_edit)
workflow.add_node("cancel", cancel)
workflow.add_edge(START, "suggest_edit")
workflow.add_edge("suggest_edit", "approve_edit")
workflow.add_edge("approve_edit", "make_edit")
workflow.add_edge("make_edit", END)
workflow.add_edge("cancel", END)
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)



router = APIRouter(prefix="/api", tags=["test"])


@router.get("/test")
async def api_test():

    async for mode, chunk in graph.astream(
        {"document": "Cats are better than dogs."}, 
        stream_mode=["messages", "updates"],
        config=config
    ):
    
        if mode == "messages":
            msg, _ = chunk
            if isinstance(msg, AIMessageChunk) and msg.content:
                print(msg.content, end="")
        
        elif mode == "updates":
            if "__interrupt__" in chunk:
                print("\ninterrupted, breaking. waiting for user approval.")
                break

            else:
                pass
                # print("state update: ", chunk)


    return {"ok": True, "route": "/api/test", "state": ""}


@router.post("/approve")
async def approve():
    async for mode, chunk in graph.astream(
        Command(resume=True),
        stream_mode=["messages", "updates"],
        config=config
    ):
        if mode == "messages":
            msg, _ = chunk
            if isinstance(msg, AIMessageChunk) and msg.content:
                print(msg.content, end="")

        elif mode == "updates":
            print("state update: ", chunk)

    return {"ok": True, "route": "/api/approve", "state": ""}