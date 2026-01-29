from fastapi import APIRouter, Request

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
import uuid
from app.agents.main import build_workflow
from app.db.URL import DB_URL

router = APIRouter(prefix="/api", tags=["test"])



@router.post("/chat/{thread_id}")
async def api_chat(request: Request, thread_id: str):

    # TODO: this is a temporary solution to get a thread id for the chat
    thread_id = str(uuid.uuid4())

    with PostgresSaver.from_conn_string(DB_URL+"?sslmode=disable") as checkpointer:

        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        state_update = {
            "thread_id": thread_id,
            "messages": [
                HumanMessage(content="I want to build a meme cat app") # TODO: persist this message as well
            ],
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

