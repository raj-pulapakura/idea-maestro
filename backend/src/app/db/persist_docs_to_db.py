from __future__ import annotations

from typing import Dict, Optional, TypedDict

import psycopg


class PersistedDoc(TypedDict, total=False):
    title: str
    content: str
    description: str
    version: int
    updated_by: Optional[str]
    updated_at: Optional[str]


def persist_docs_to_db(
    conn: psycopg.Connection,
    thread_id: str,
    docs: Dict[str, PersistedDoc],
    *,
    change_set_id: str | None = None,
    summary: str = "",
) -> int:
    if not docs:
        raise ValueError("docs is empty")

    with conn.transaction():
        with conn.cursor() as cur:
            for doc_id, payload in docs.items():
                try:
                    content = payload["content"]
                    description = payload.get("description", "")
                except KeyError as e:
                    raise KeyError(f"doc {doc_id!r} is missing required field {e.args[0]!r}") from e

                title = payload.get("title", doc_id.replace("_", " ").title())
                updated_by = payload.get("updated_by")
                updated_at = payload.get("updated_at")

                cur.execute(
                    """
                    SELECT content, version
                    FROM docs
                    WHERE thread_id = %s AND doc_id = %s
                    """,
                    (thread_id, doc_id),
                )
                existing = cur.fetchone()

                if existing:
                    old_content, old_version = existing
                    content_changed = old_content != content
                    next_version = old_version + 1 if content_changed else old_version
                    cur.execute(
                        """
                        UPDATE docs
                        SET
                          title = %s,
                          content = %s,
                          description = %s,
                          version = %s,
                          updated_by = %s,
                          updated_at = COALESCE(%s::timestamptz, NOW())
                        WHERE thread_id = %s AND doc_id = %s
                        """,
                        (
                            title,
                            content,
                            description,
                            next_version,
                            updated_by,
                            updated_at,
                            thread_id,
                            doc_id,
                        ),
                    )

                    if content_changed:
                        cur.execute(
                            """
                            INSERT INTO doc_versions (
                              thread_id,
                              doc_id,
                              version,
                              content,
                              summary,
                              updated_by,
                              change_set_id
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                thread_id,
                                doc_id,
                                next_version,
                                content,
                                summary,
                                updated_by,
                                change_set_id,
                            ),
                        )
                    continue

                initial_version = payload.get("version", 1)
                cur.execute(
                    """
                    INSERT INTO docs (
                      thread_id,
                      doc_id,
                      title,
                      content,
                      description,
                      version,
                      updated_by,
                      updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s::timestamptz, NOW()))
                    """,
                    (
                        thread_id,
                        doc_id,
                        title,
                        content,
                        description,
                        initial_version,
                        updated_by,
                        updated_at,
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO doc_versions (
                      thread_id,
                      doc_id,
                      version,
                      content,
                      summary,
                      updated_by,
                      change_set_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        thread_id,
                        doc_id,
                        initial_version,
                        content,
                        summary,
                        updated_by,
                        change_set_id,
                    ),
                )

    return len(docs)

