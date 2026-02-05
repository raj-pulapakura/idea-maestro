from typing import List, Tuple, Dict, Any
import json
import psycopg


def persist_messages_to_db(
    conn: psycopg.Connection, 
    thread_id: str, 
    messages: List[Dict[str, Any]]
) -> Tuple[int, int]:
    if not messages:
        raise ValueError("messages is empty")

    n = len(messages)

    with conn.transaction():
        with conn.cursor() as cur:
            # Ensure thread exists
            cur.execute(
                "INSERT INTO chat_threads(thread_id) VALUES (%s) ON CONFLICT (thread_id) DO NOTHING;",
                (thread_id,),
            )

            # Reserve seq block
            cur.execute(
                """
                UPDATE chat_threads
                SET next_seq = next_seq + %s
                WHERE thread_id = %s
                RETURNING next_seq - %s;
                """,
                (n, thread_id, n),
            )
            start_seq = cur.fetchone()[0]

            # Batch insert
            rows = []
            for i, m in enumerate(messages):
                seq = start_seq + i
                rows.append((
                    thread_id,
                    seq,
                    m["role"],
                    m.get("type"),
                    json.dumps(m["content"]),
                    m.get("name"),
                    m.get("tool_call_id"),
                    json.dumps(m.get("tool_calls")) if m.get("tool_calls") is not None else None,
                    json.dumps(m.get("metadata", {})),
                    m.get("by_agent"),
                ))

            cur.executemany(
                """
                INSERT INTO chat_messages (
                  thread_id, seq, role, type, content, name, tool_call_id, tool_calls, metadata, by_agent
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s::jsonb, %s);
                """,
                rows,
            )

    end_seq = start_seq + n - 1
    return start_seq, end_seq