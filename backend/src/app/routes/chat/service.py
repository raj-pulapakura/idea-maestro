from __future__ import annotations

from typing import Any, Iterator

from langchain_core.messages import HumanMessage

from app.agents.build_workflow import build_workflow
from app.agents.state.empty_docs import empty_docs
from app.agents.state.get_initial_state_update import get_initial_state_update
from app.db.checkpoint import checkpoint_db_url
from app.db.fetch_thread_docs import fetch_thread_docs_map
from app.db.get_conn_factory import conn_factory
from app.db.lc_message_to_row import lc_message_to_row
from app.db.persist_docs_to_db import persist_docs_to_db
from app.db.persist_messages_to_db import persist_messages_to_db
from app.db.thread_repository import (
    ensure_thread,
    mark_docs_bootstrapped,
    needs_docs_bootstrap,
)
from langgraph.checkpoint.postgres import PostgresSaver
from .streaming import stream_graph_events


def persist_user_chat_message(thread_id: str, message: str, *, run_id: str) -> HumanMessage:
    ensure_thread(thread_id)
    user_message = HumanMessage(content=message)
    with conn_factory() as conn:
        persist_messages_to_db(
            conn,
            thread_id,
            [lc_message_to_row(user_message)],
            run_id=run_id,
        )
    return user_message


def ensure_thread_documents(thread_id: str) -> None:
    if not needs_docs_bootstrap(thread_id):
        return

    ensure_thread(thread_id)
    with conn_factory() as conn:
        persist_docs_to_db(conn, thread_id, empty_docs)
    mark_docs_bootstrapped(thread_id)


def _load_thread_docs(thread_id: str) -> dict[str, Any]:
    with conn_factory() as conn:
        docs = fetch_thread_docs_map(conn, thread_id)
    return docs or empty_docs


def build_initial_chat_state(
    *,
    thread_id: str,
    run_id: str,
    user_message: HumanMessage,
) -> dict[str, Any]:
    return get_initial_state_update(
        thread_id=thread_id,
        run_id=run_id,
        user_message=user_message,
        docs=_load_thread_docs(thread_id),
    )


def graph_event_stream(
    *,
    thread_id: str,
    run_id: str,
    graph_input: dict[str, Any] | Any,
    trigger: str,
) -> Iterator[str]:
    with PostgresSaver.from_conn_string(checkpoint_db_url()) as checkpointer:
        checkpointer.setup()
        workflow = build_workflow()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        yield from stream_graph_events(
            graph_input=graph_input,
            config=config,
            thread_id=thread_id,
            run_id=run_id,
            trigger=trigger,
            graph=graph,
        )
