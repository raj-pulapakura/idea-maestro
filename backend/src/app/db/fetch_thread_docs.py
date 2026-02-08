from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row


def fetch_thread_docs(conn, thread_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
              thread_id,
              doc_id,
              title,
              content,
              description,
              version,
              updated_by,
              updated_at,
              created_at
            FROM docs
            WHERE thread_id = %s
            ORDER BY doc_id ASC
            """,
            (thread_id,),
        )
        return cur.fetchall()


def fetch_thread_doc(conn, thread_id: str, doc_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
              thread_id,
              doc_id,
              title,
              content,
              description,
              version,
              updated_by,
              updated_at,
              created_at
            FROM docs
            WHERE thread_id = %s AND doc_id = %s
            LIMIT 1
            """,
            (thread_id, doc_id),
        )
        return cur.fetchone()


def fetch_thread_docs_map(conn, thread_id: str) -> dict[str, dict[str, Any]]:
    rows = fetch_thread_docs(conn, thread_id)
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        mapped[row["doc_id"]] = {
            "title": row["title"],
            "content": row["content"],
            "description": row["description"],
            "version": row["version"],
            "updated_by": row["updated_by"],
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }
    return mapped
