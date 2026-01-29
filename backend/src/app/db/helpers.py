from typing import Any, Callable, Dict, List, Optional, Tuple
import json
import psycopg
from psycopg.rows import dict_row
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.types import Command

MessageRow = Dict[str, Any]

def append_messages(conn: psycopg.Connection, thread_id: str, messages: List[MessageRow]) -> Tuple[int, int]:
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
                ))

            cur.executemany(
                """
                INSERT INTO chat_messages (
                  thread_id, seq, role, type, content, name, tool_call_id, tool_calls, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s::jsonb);
                """,
                rows,
            )

    end_seq = start_seq + n - 1
    return start_seq, end_seq


def fetch_thread_messages(conn: psycopg.Connection, thread_id: str):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT role, type, content, name, tool_call_id, tool_calls, metadata, created_at
            FROM chat_messages
            WHERE thread_id = %s
            ORDER BY seq ASC
            """,
            (thread_id,),
        )
        return cur.fetchall()


def lc_message_to_row(msg: BaseMessage) -> Dict[str, Any]:
    """
    Convert a LangChain message object to a UI-friendly row payload.
    Keeps tool_calls + tool_call_id linkage for rendering.
    """
    role = getattr(msg, "type", None)  # "human", "ai", "tool", "system"
    role_map = {"human": "user", "ai": "assistant", "tool": "tool", "system": "system"}
    ui_role = role_map.get(role, "assistant")

    # Content can be str or list of blocks depending on provider/version
    print("msg: ", msg)
    content = msg.content

    row: Dict[str, Any] = {
        "role": ui_role,
        "type": msg.__class__.__name__,
        "content": {"text": content} if isinstance(content, str) else {"blocks": content},
        "metadata": msg.additional_kwargs or {},
    }

    # Tool calls live on AIMessage in most LC versions
    if isinstance(msg, AIMessage):
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            row["tool_calls"] = tool_calls

    # Tool results are ToolMessage with tool_call_id + name
    if isinstance(msg, ToolMessage):
        row["tool_call_id"] = getattr(msg, "tool_call_id", None)
        row["name"] = getattr(msg, "name", None)

    return row

def _extract_update_from_node_output(out: Any) -> Optional[Dict[str, Any]]:
    """
    Normalize node output into a state-update dict (if present).
    - If out is a dict: that's the update.
    - If out is a Command: use out.update (if any).
    - Otherwise: no update.
    """
    if isinstance(out, dict):
        return out

    if isinstance(out, Command):
        upd = getattr(out, "update", None)
        if upd is None:
            return None
        if not isinstance(upd, dict):
            raise TypeError(f"Command.update must be a dict, got {type(upd)}")
        return upd

    return None

def persist_messages_wrapper(
    node_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    *,
    conn_factory: Callable[[], psycopg.Connection],
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Wrap a LangGraph node. If it returns {"messages": [...]}, persist those messages to Postgres.
    """
    def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
        out = node_fn(state)

        update = _extract_update_from_node_output(out)
        if not update:
            return out

        new_msgs = update.get("messages")
        if not new_msgs:
            return out

        if not isinstance(new_msgs, list):
            new_msgs = [new_msgs]

        rows = [lc_message_to_row(m) for m in new_msgs]
        thread_id = state["thread_id"]

        with conn_factory() as conn:
            append_messages(conn, thread_id, rows)

        return out

    return wrapped