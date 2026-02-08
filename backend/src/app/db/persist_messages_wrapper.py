from typing import Dict, Any, Optional, Callable
import psycopg
from langgraph.types import Command
from app.db.persist_messages_to_db import persist_messages_to_db
from app.db.lc_message_to_row import lc_message_to_row

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
    Wrap a LangGraph node. If it returns {"messages": [...], "by_agent": ...}, persist those messages to Postgres.
    """
    def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
        out = node_fn(state)

        update = _extract_update_from_node_output(out)
        if not update:
            return out

        by_agent = update.get("by_agent")
        new_msgs = update.get("messages")
        if not new_msgs:
            return out

        if not isinstance(new_msgs, list):
            new_msgs = [new_msgs]

        rows = [lc_message_to_row(m, by_agent) for m in new_msgs]
        thread_id = state["thread_id"]
        run_id = state.get("run_id")

        with conn_factory() as conn:
            persist_messages_to_db(conn, thread_id, rows, run_id=run_id)

        return out

    return wrapped
