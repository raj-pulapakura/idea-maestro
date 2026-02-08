from typing import List, Dict, Any
import json
import psycopg
from psycopg.rows import dict_row


def fetch_thread_messages(conn: psycopg.Connection, thread_id: str) -> List[Dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
              message_id,
              thread_id,
              run_id,
              seq,
              role,
              type,
              content,
              name,
              tool_call_id,
              tool_calls,
              metadata,
              created_at,
              by_agent
            FROM chat_messages
            WHERE thread_id = %s
            ORDER BY seq ASC
            """,
            (thread_id,),
        )
        return cur.fetchall()
