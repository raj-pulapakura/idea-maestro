from typing import Dict, TypedDict

import psycopg


class PersistedDoc(TypedDict):
    content: str
    description: str


def persist_docs_to_db(
    conn: psycopg.Connection,
    thread_id: str,
    docs: Dict[str, PersistedDoc],
) -> int:
    """
    Persist docs for a thread into the `docs` table (SCD1 style: overwrite in place).

    Expects `docs` to be a mapping of doc_id -> { "content": str, "description": str, ... }.

    DDL reference (see notes.txt:111-117):
        create table if not exists docs (
          id bigserial primary key,
          thread_id text not null,
          doc_id text not null,
          content text not null,
          description text not null
        );
    """
    if not docs:
        raise ValueError("docs is empty")

    with conn.transaction():
        with conn.cursor() as cur:
            for doc_id, payload in docs.items():
                try:
                    content = payload["content"]
                    description = payload["description"]
                except KeyError as e:
                    raise KeyError(f"doc {doc_id!r} is missing required field {e.args[0]!r}") from e

                # First try to update an existing row for (thread_id, doc_id)
                cur.execute(
                    """
                    UPDATE docs
                    SET content = %s,
                        description = %s
                    WHERE thread_id = %s
                      AND doc_id = %s;
                    """,
                    (content, description, thread_id, doc_id),
                )

                # If no row was updated, insert a new one
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO docs (
                          thread_id,
                          doc_id,
                          content,
                          description
                        ) VALUES (%s, %s, %s, %s);
                        """,
                        (thread_id, doc_id, content, description),
                    )

    return len(docs)


