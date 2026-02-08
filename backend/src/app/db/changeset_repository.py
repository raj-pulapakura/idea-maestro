from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row

from app.db.get_conn_factory import conn_factory


def create_changeset(
    *,
    change_set_id: str,
    thread_id: str,
    run_id: str | None,
    created_by: str,
    summary: str,
    docs: list[dict[str, str]],
    status: str = "pending",
) -> None:
    with conn_factory() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO change_sets (
                      change_set_id,
                      thread_id,
                      run_id,
                      created_by,
                      summary,
                      status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (change_set_id) DO NOTHING
                    """,
                    (change_set_id, thread_id, run_id, created_by, summary, status),
                )

                for doc in docs:
                    cur.execute(
                        """
                        INSERT INTO change_set_docs (
                          change_set_id,
                          thread_id,
                          doc_id,
                          before_content,
                          after_content,
                          diff
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (change_set_id, doc_id)
                        DO UPDATE SET
                          before_content = EXCLUDED.before_content,
                          after_content = EXCLUDED.after_content,
                          diff = EXCLUDED.diff
                        """,
                        (
                            change_set_id,
                            thread_id,
                            doc["doc_id"],
                            doc["before_content"],
                            doc["after_content"],
                            doc["diff"],
                        ),
                    )


def set_changeset_status(
    change_set_id: str,
    *,
    status: str,
    decision_note: str | None = None,
    decided: bool = False,
) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE change_sets
                SET
                  status = %s,
                  decision_note = COALESCE(%s, decision_note),
                  decided_at = CASE WHEN %s THEN NOW() ELSE decided_at END
                WHERE change_set_id = %s
                """,
                (status, decision_note, decided, change_set_id),
            )
        conn.commit()


def append_changeset_review(
    change_set_id: str,
    *,
    decision: str,
    comment: str | None = None,
    reviewed_by: str | None = "user",
) -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO change_set_reviews (change_set_id, decision, comment, reviewed_by)
                VALUES (%s, %s, %s, %s)
                """,
                (change_set_id, decision, comment, reviewed_by),
            )
        conn.commit()


def fetch_changesets(thread_id: str) -> list[dict[str, Any]]:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  change_set_id,
                  thread_id,
                  run_id,
                  created_by,
                  summary,
                  status,
                  created_at,
                  decided_at,
                  decision_note
                FROM change_sets
                WHERE thread_id = %s
                ORDER BY created_at ASC
                """,
                (thread_id,),
            )
            changesets = cur.fetchall()

            for changeset in changesets:
                cur.execute(
                    """
                    SELECT doc_id, before_content, after_content, diff
                    FROM change_set_docs
                    WHERE change_set_id = %s
                    ORDER BY doc_id ASC
                    """,
                    (changeset["change_set_id"],),
                )
                doc_rows = cur.fetchall()
                changeset["docs"] = [doc["doc_id"] for doc in doc_rows]
                changeset["diffs"] = {doc["doc_id"]: doc["diff"] for doc in doc_rows}

            return changesets


def fetch_changeset_detail(thread_id: str, change_set_id: str) -> dict[str, Any] | None:
    with conn_factory() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  change_set_id,
                  thread_id,
                  run_id,
                  created_by,
                  summary,
                  status,
                  created_at,
                  decided_at,
                  decision_note
                FROM change_sets
                WHERE thread_id = %s AND change_set_id = %s
                LIMIT 1
                """,
                (thread_id, change_set_id),
            )
            changeset = cur.fetchone()
            if not changeset:
                return None

            cur.execute(
                """
                SELECT
                  doc_id,
                  before_content,
                  after_content,
                  diff
                FROM change_set_docs
                WHERE change_set_id = %s
                ORDER BY doc_id ASC
                """,
                (change_set_id,),
            )
            doc_rows = cur.fetchall()
            changeset["docs"] = [doc["doc_id"] for doc in doc_rows]
            changeset["diffs"] = {doc["doc_id"]: doc["diff"] for doc in doc_rows}
            changeset["doc_changes"] = doc_rows

            cur.execute(
                """
                SELECT
                  decision,
                  comment,
                  reviewed_by,
                  reviewed_at
                FROM change_set_reviews
                WHERE change_set_id = %s
                ORDER BY reviewed_at ASC
                """,
                (change_set_id,),
            )
            changeset["reviews"] = cur.fetchall()

            return changeset
