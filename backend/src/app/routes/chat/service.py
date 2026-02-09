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

LEGACY_TO_V2_DOC_ID = {
    "the_pitch": "product_brief",
    "risk_register": "risk_decision_log",
    "business_model": "business_model_pricing",
    "feature_roadmap": "mvp_scope_non_goals",
    "gtm_plan": "gtm_plan",
    "technical_spec": "technical_plan",
    "competitor_analysis": "evidence_assumptions_log",
    "open_questions": "next_actions_board",
}


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
        _migrate_legacy_documents_if_needed(thread_id)
        return

    ensure_thread(thread_id)
    with conn_factory() as conn:
        persist_docs_to_db(conn, thread_id, empty_docs)
    mark_docs_bootstrapped(thread_id)


def _load_thread_docs(thread_id: str) -> dict[str, Any]:
    with conn_factory() as conn:
        docs = fetch_thread_docs_map(conn, thread_id)
    return docs or empty_docs


def _migrate_legacy_documents_if_needed(thread_id: str) -> None:
    with conn_factory() as conn:
        docs = fetch_thread_docs_map(conn, thread_id)
        if not docs:
            return

        legacy_ids = set(LEGACY_TO_V2_DOC_ID.keys()) & set(docs.keys())
        if not legacy_ids:
            return

        has_v2_docs = any(doc_id in docs for doc_id in empty_docs)
        if has_v2_docs:
            return

        migrated_docs = {doc_id: dict(payload) for doc_id, payload in empty_docs.items()}

        for legacy_doc_id, v2_doc_id in LEGACY_TO_V2_DOC_ID.items():
            legacy_doc = docs.get(legacy_doc_id)
            if not legacy_doc:
                continue
            migrated_docs[v2_doc_id]["content"] = legacy_doc.get("content", "")
            migrated_docs[v2_doc_id]["updated_by"] = legacy_doc.get("updated_by")
            migrated_docs[v2_doc_id]["updated_at"] = legacy_doc.get("updated_at")
            if isinstance(legacy_doc.get("version"), int):
                migrated_docs[v2_doc_id]["version"] = legacy_doc["version"]

        with conn.transaction():
            persist_docs_to_db(conn, thread_id, migrated_docs)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM docs
                    WHERE thread_id = %s AND doc_id = ANY(%s)
                    """,
                    (thread_id, list(legacy_ids)),
                )


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
