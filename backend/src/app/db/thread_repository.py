from __future__ import annotations

from functools import lru_cache
from typing import Any

from psycopg.rows import dict_row

from app.db.get_conn_factory import conn_factory


def ensure_thread(thread_id: str) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_threads (thread_id)
                VALUES (%s)
                ON CONFLICT (thread_id) DO NOTHING
                """,
                (thread_id,),
            )
        conn.commit()


def thread_exists(thread_id: str) -> bool:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM chat_threads WHERE thread_id = %s LIMIT 1",
                (thread_id,),
            )
            return cur.fetchone() is not None


def fetch_thread(thread_id: str) -> dict[str, Any] | None:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  thread_id,
                  title,
                  status,
                  created_at,
                  updated_at,
                  last_message_preview
                FROM chat_threads
                WHERE thread_id = %s
                """,
                (thread_id,),
            )
            return cur.fetchone()


def touch_thread(
    thread_id: str,
    *,
    last_message_preview: str | None = None,
) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_threads
                SET
                  updated_at = NOW(),
                  last_message_preview = COALESCE(%s, last_message_preview)
                WHERE thread_id = %s
                """,
                (last_message_preview, thread_id),
            )
        conn.commit()


def list_threads(*, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  thread_id,
                  title,
                  status,
                  created_at,
                  updated_at,
                  last_message_preview
                FROM chat_threads
                ORDER BY updated_at DESC, created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            return cur.fetchall()


def create_thread(
    *,
    thread_id: str,
    title: str | None = None,
    status: str = "active",
) -> dict[str, Any]:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO chat_threads (thread_id, title, status)
                VALUES (%s, COALESCE(%s, 'Untitled Thread'), %s)
                ON CONFLICT (thread_id) DO UPDATE
                SET
                  title = chat_threads.title,
                  status = chat_threads.status
                RETURNING
                  thread_id,
                  title,
                  status,
                  created_at,
                  updated_at,
                  last_message_preview
                """,
                (thread_id, title, status),
            )
            row = cur.fetchone()
        conn.commit()
    return row


def update_thread(
    thread_id: str,
    *,
    title: str | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE chat_threads
                SET
                  title = COALESCE(%s, title),
                  status = COALESCE(%s, status),
                  updated_at = NOW()
                WHERE thread_id = %s
                RETURNING
                  thread_id,
                  title,
                  status,
                  created_at,
                  updated_at,
                  last_message_preview
                """,
                (title, status, thread_id),
            )
            row = cur.fetchone()
        conn.commit()
    return row


def needs_docs_bootstrap(thread_id: str) -> bool:
    if not _has_docs_initialized_column():
        return _needs_docs_bootstrap_without_column(thread_id)

    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT docs_initialized
                FROM chat_threads
                WHERE thread_id = %s
                """,
                (thread_id,),
            )
            row = cur.fetchone()
            if row is None:
                return True
            return not row[0]


def mark_docs_bootstrapped(thread_id: str) -> None:
    if not _has_docs_initialized_column():
        return

    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_threads
                SET
                  docs_initialized = TRUE,
                  updated_at = NOW()
                WHERE thread_id = %s
                """,
                (thread_id,),
            )
        conn.commit()


@lru_cache(maxsize=1)
def _has_docs_initialized_column() -> bool:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1
                  FROM information_schema.columns
                  WHERE table_schema = 'public'
                    AND table_name = 'chat_threads'
                    AND column_name = 'docs_initialized'
                )
                """
            )
            row = cur.fetchone()
            return bool(row and row[0])


def _needs_docs_bootstrap_without_column(thread_id: str) -> bool:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM chat_threads WHERE thread_id = %s
                )
                """,
                (thread_id,),
            )
            thread_row = cur.fetchone()
            thread_exists = bool(thread_row and thread_row[0])
            if not thread_exists:
                return True

            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM docs WHERE thread_id = %s
                )
                """,
                (thread_id,),
            )
            docs_row = cur.fetchone()
            has_docs = bool(docs_row and docs_row[0])
            return not has_docs
