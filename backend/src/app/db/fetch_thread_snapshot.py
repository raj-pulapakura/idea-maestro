from __future__ import annotations

from typing import Any

from app.db.fetch_thread_docs import fetch_thread_docs
from app.db.fetch_thread_messages import fetch_thread_messages
from app.db.run_repository import fetch_latest_agent_statuses, fetch_runs
from app.db.changeset_repository import fetch_changesets
from app.db.thread_repository import fetch_thread


def _serialize_timestamps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for row in rows:
        out: dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                out[key] = value.isoformat()
            else:
                out[key] = value
        serialized.append(out)
    return serialized


def fetch_thread_snapshot(conn, thread_id: str) -> dict[str, Any]:
    thread = fetch_thread(thread_id)
    messages = fetch_thread_messages(conn, thread_id)
    docs = fetch_thread_docs(conn, thread_id)
    runs = fetch_runs(thread_id)
    agent_statuses = fetch_latest_agent_statuses(thread_id)
    changesets = fetch_changesets(thread_id)

    return {
        "thread": _serialize_timestamps([thread])[0] if thread else None,
        "messages": _serialize_timestamps(messages),
        "docs": _serialize_timestamps(docs),
        "runs": _serialize_timestamps(runs),
        "agent_statuses": _serialize_timestamps(agent_statuses),
        "changesets": _serialize_timestamps(changesets),
    }
