from typing import Any, Iterator

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

from app.agents.build_workflow import build_workflow
from app.agents.state.empty_docs import empty_docs
from app.agents.state.get_initial_state_update import get_initial_state_update
from app.db.URL import DB_URL
from app.db.fetch_thread_messages import fetch_thread_messages
from app.db.get_conn_factory import conn_factory
from app.db.lc_message_to_row import lc_message_to_row
from app.db.persist_docs_to_db import persist_docs_to_db
from app.db.persist_messages_to_db import persist_messages_to_db
from .streaming import stream_graph_events


def thread_exists(thread_id: str) -> bool:
    with conn_factory() as conn:
        return len(fetch_thread_messages(conn, thread_id)) > 0


def persist_user_chat_message(thread_id: str, message: str) -> HumanMessage:
    user_message = HumanMessage(content=message)
    persist_messages_to_db(conn_factory(), thread_id, [lc_message_to_row(user_message)])
    return user_message


def ensure_thread_documents(thread_id: str, is_new_thread: bool):
    if is_new_thread:
        persist_docs_to_db(conn_factory(), thread_id, empty_docs)


def build_initial_chat_state(
    *,
    thread_id: str,
    is_new_thread: bool,
    user_message: HumanMessage,
) -> dict[str, Any]:
    return get_initial_state_update(is_new_thread, thread_id, user_message)


def graph_event_stream(
    *,
    thread_id: str,
    graph_input: dict[str, Any] | Any,
    emit_thread_started: bool,
) -> Iterator[str]:
    with PostgresSaver.from_conn_string(DB_URL + "?sslmode=disable") as checkpointer:
        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        yield from stream_graph_events(
            graph_input=graph_input,
            config=config,
            thread_id=thread_id,
            graph=graph,
            emit_thread_started=emit_thread_started,
        )
