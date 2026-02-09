from typing import Dict, Any, Optional, Callable
import psycopg
from psycopg import errors as psycopg_errors
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


def _invoke_node(node_fn: Any, state: Dict[str, Any]) -> Any:
    if callable(node_fn):
        return node_fn(state)
    invoke = getattr(node_fn, "invoke", None)
    if callable(invoke):
        return invoke(state)
    raise TypeError(f"Unsupported node type for persistence adapter: {type(node_fn)}")


def _resolve_by_agent(update: Dict[str, Any], agent_name: str | None) -> str:
    by_agent = update.get("by_agent")
    if isinstance(by_agent, str) and by_agent.strip():
        return by_agent.strip()
    if isinstance(agent_name, str) and agent_name.strip():
        return agent_name.strip()
    return "agent"


def _message_fingerprint(message: Any) -> tuple[Any, ...]:
    return (
        getattr(message, "type", None),
        getattr(message, "id", None),
        getattr(message, "name", None),
        getattr(message, "tool_call_id", None),
        repr(getattr(message, "content", None)),
    )


def _extract_new_messages(state: Dict[str, Any], update: Dict[str, Any]) -> list[Any]:
    raw_messages = update.get("messages")
    if not raw_messages:
        return []

    update_messages = raw_messages if isinstance(raw_messages, list) else [raw_messages]
    state_messages = state.get("messages") or []
    if not isinstance(state_messages, list):
        state_messages = []

    if len(update_messages) < len(state_messages):
        return update_messages

    prefix_matches = all(
        _message_fingerprint(update_messages[idx]) == _message_fingerprint(state_messages[idx])
        for idx in range(len(state_messages))
    )
    if not prefix_matches:
        return update_messages

    return update_messages[len(state_messages):]


def _resolve_message_by_agent(message: Any, default_agent: str) -> str:
    role = getattr(message, "type", None)
    if role == "human":
        return "user"
    if role == "system":
        return "system"
    return default_agent


def persist_messages_adapter(
    node_fn: Callable[[Dict[str, Any]], Any] | Any,
    *,
    conn_factory: Callable[[], psycopg.Connection],
    agent_name: str | None = None,
    should_persist: Callable[[Dict[str, Any], Dict[str, Any]], bool] | None = None,
) -> Callable[[Dict[str, Any]], Any]:
    """
    Wrap any graph node/runnable.
    If the node output contains update.messages, persist those messages to Postgres.
    """
    def wrapped(state: Dict[str, Any]) -> Any:
        out = _invoke_node(node_fn, state)

        update = _extract_update_from_node_output(out)
        if not update:
            return out

        if should_persist is not None and not should_persist(state, update):
            return out

        default_by_agent = _resolve_by_agent(update, agent_name)
        new_msgs = _extract_new_messages(state, update)
        if not new_msgs:
            return out

        rows = [
            lc_message_to_row(message, _resolve_message_by_agent(message, default_by_agent))
            for message in new_msgs
        ]
        thread_id = state["thread_id"]
        run_id = state.get("run_id")

        try:
            with conn_factory() as conn:
                persist_messages_to_db(conn, thread_id, rows, run_id=run_id)
        except psycopg_errors.UniqueViolation:
            # Duplicate message writes are safe to ignore for idempotent retries.
            return out

        return out

    return wrapped


def persist_messages_wrapper(
    node_fn: Callable[[Dict[str, Any]], Any] | Any,
    *,
    conn_factory: Callable[[], psycopg.Connection],
) -> Callable[[Dict[str, Any]], Any]:
    """
    Backward-compatible alias used by existing workflow code.
    """
    return persist_messages_adapter(node_fn, conn_factory=conn_factory)
