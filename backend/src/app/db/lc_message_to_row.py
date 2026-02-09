from __future__ import annotations

from typing import Dict, Any, Optional
import uuid
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

def lc_message_to_row(msg: BaseMessage, by_agent: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a LangChain message object to a UI-friendly row payload.
    Keeps tool_calls + tool_call_id linkage for rendering.
    """
    role = getattr(msg, "type", None)  # "human", "ai", "tool", "system"
    role_map = {"human": "user", "ai": "assistant", "tool": "tool", "system": "system"}
    ui_role = role_map.get(role, "assistant")

    # Content can be str or list of blocks depending on provider/version
    content = msg.content

    normalized_by_agent: Optional[str]
    if isinstance(by_agent, str) and by_agent.strip():
        normalized_by_agent = by_agent.strip()
    elif ui_role == "user":
        normalized_by_agent = "user"
    elif ui_role == "system":
        normalized_by_agent = "system"
    else:
        normalized_by_agent = None

    row: Dict[str, Any] = {
        "message_id": getattr(msg, "id", None) or str(uuid.uuid4()),
        "role": ui_role,
        "type": msg.__class__.__name__,
        "content": {"text": content} if isinstance(content, str) else {"blocks": content},
        "metadata": msg.additional_kwargs or {},
        "by_agent": normalized_by_agent,
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
