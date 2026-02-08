import json
from typing import Any, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from app.db.lc_message_to_row import lc_message_to_row


def make_json_serializable(obj: Any):
    """Recursively convert objects to JSON-serializable format."""
    if isinstance(obj, BaseMessage):
        return lc_message_to_row(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return make_json_serializable(obj.__dict__)

    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue

        if not isinstance(block, dict):
            continue

        text_value = block.get("text")
        if isinstance(text_value, str):
            parts.append(text_value)
            continue
        if isinstance(text_value, dict):
            nested_text = text_value.get("value")
            if isinstance(nested_text, str):
                parts.append(nested_text)
                continue

        if isinstance(block.get("content"), str):
            parts.append(block["content"])

    return "".join(parts)


def normalize_tool_calls(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []

    raw_calls = raw if isinstance(raw, list) else [raw]
    normalized: list[dict[str, Any]] = []

    for item in raw_calls:
        if isinstance(item, dict):
            normalized.append(item)
            continue
        if isinstance(item, BaseModel):
            normalized.append(item.model_dump())
            continue
        if hasattr(item, "model_dump") and callable(item.model_dump):
            normalized.append(item.model_dump())
            continue
        if hasattr(item, "__dict__"):
            normalized.append(dict(item.__dict__))
            continue
        normalized.append({"value": str(item)})

    return normalized


def guess_agent_from_namespace(namespace: Any) -> Optional[str]:
    canonical_by_key = {
        "maestro": "maestro",
        "devil's advocate": "Devil's Advocate",
        "angel eyes": "Angel Eyes",
        "capital freak": "Capital Freak",
        "cake man": "Cake Man",
        "buzz": "Buzz",
        "mr. t": "Mr. T",
    }

    strings: list[str] = []

    def _scan(value: Any):
        if isinstance(value, str):
            strings.append(value)
            return
        if isinstance(value, (list, tuple)):
            for nested in value:
                _scan(nested)

    _scan(namespace)

    for candidate in reversed(strings):
        key = candidate.strip().lower()
        if key in canonical_by_key:
            return canonical_by_key[key]

    return None


def find_approval_interrupt(updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    raw_interrupt = updates.get("__interrupt__")
    if raw_interrupt is None:
        return None

    candidates = raw_interrupt if isinstance(raw_interrupt, list) else [raw_interrupt]
    for candidate in candidates:
        if isinstance(candidate, dict):
            value = candidate.get("value", candidate)
            if isinstance(value, dict) and value.get("type") == "approval_required":
                return value
            if candidate.get("type") == "approval_required":
                return candidate

    return {"type": "approval_required", "value": make_json_serializable(raw_interrupt)}
