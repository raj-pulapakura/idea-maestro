from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from psycopg.rows import dict_row

from app.db.get_conn_factory import conn_factory

RunStatus = Literal["queued", "running", "waiting_approval", "completed", "error"]
AgentStatus = Literal[
    "queued",
    "thinking",
    "tool_call",
    "waiting_approval",
    "done",
    "error",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run(
    *,
    run_id: str,
    thread_id: str,
    trigger: str,
    status: RunStatus = "queued",
) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (run_id, thread_id, trigger, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (run_id) DO NOTHING
                """,
                (run_id, thread_id, trigger, status),
            )
        conn.commit()


def set_run_status(
    run_id: str,
    *,
    status: RunStatus,
    error: str | None = None,
    completed: bool = False,
) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET
                  status = %s,
                  error = COALESCE(%s, error),
                  completed_at = CASE WHEN %s THEN NOW() ELSE completed_at END
                WHERE run_id = %s
                """,
                (status, error, completed, run_id),
            )
        conn.commit()


def append_agent_status(
    *,
    run_id: str,
    thread_id: str,
    agent: str,
    status: AgentStatus,
    note: str | None = None,
) -> dict[str, Any]:
    created_at = _now_iso()
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_status_events (run_id, thread_id, agent, status, note)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (run_id, thread_id, agent, status, note),
            )
        conn.commit()

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "agent": agent,
        "status": status,
        "note": note,
        "at": created_at,
    }


def fetch_runs(thread_id: str) -> list[dict[str, Any]]:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT run_id, thread_id, trigger, status, started_at, completed_at, error
                FROM runs
                WHERE thread_id = %s
                ORDER BY started_at ASC
                """,
                (thread_id,),
            )
            return cur.fetchall()


def fetch_latest_agent_statuses(thread_id: str) -> list[dict[str, Any]]:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (run_id, agent)
                  run_id,
                  thread_id,
                  agent,
                  status,
                  note,
                  created_at AS at
                FROM agent_status_events
                WHERE thread_id = %s
                ORDER BY run_id, agent, created_at DESC
                """,
                (thread_id,),
            )
            return cur.fetchall()
