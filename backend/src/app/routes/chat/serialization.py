import json
import re
from ast import literal_eval
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
        "devils_advocate": "Devil's Advocate",
        "devils advocate": "Devil's Advocate",
        "angel eyes": "Angel Eyes",
        "angel_eyes": "Angel Eyes",
        "capital freak": "Capital Freak",
        "capital_freak": "Capital Freak",
        "cake man": "Cake Man",
        "cake_man": "Cake Man",
        "buzz": "Buzz",
        "mr. t": "Mr. T",
        "mr_t": "Mr. T",
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

    def normalize_approval_payload(value: Any, interrupt_id: Any = None) -> Optional[dict[str, Any]]:
        if not isinstance(value, dict):
            return None
        if value.get("type") != "approval_required":
            return None
        payload = make_json_serializable(value)
        if isinstance(interrupt_id, str) and interrupt_id:
            payload["interrupt_id"] = interrupt_id
        return payload

    def parse_interrupt_repr(text: str) -> Optional[dict[str, Any]]:
        # Fallback for LangGraph Interrupt repr strings:
        # "Interrupt(value={...}, id='abc123')"
        if not text.startswith("Interrupt("):
            return None
        match = re.search(r"Interrupt\(value=(.*),\s*id='([^']+)'\)$", text, flags=re.DOTALL)
        if not match:
            return None
        value_expr, interrupt_id = match.group(1), match.group(2)
        try:
            parsed = literal_eval(value_expr)
        except (SyntaxError, ValueError):
            return None
        return normalize_approval_payload(parsed, interrupt_id)

    candidates = raw_interrupt if isinstance(raw_interrupt, list) else [raw_interrupt]
    for candidate in candidates:
        candidate_value = getattr(candidate, "value", None)
        candidate_id = getattr(candidate, "id", None) or getattr(candidate, "interrupt_id", None)
        payload = normalize_approval_payload(candidate_value, candidate_id)
        if payload:
            return payload

        if isinstance(candidate, dict):
            interrupt_id = candidate.get("id") or candidate.get("interrupt_id")
            value = candidate.get("value", candidate)
            payload = normalize_approval_payload(value, interrupt_id)
            if payload:
                return payload
            payload = normalize_approval_payload(candidate, interrupt_id)
            if payload:
                return payload

        if isinstance(candidate, str):
            payload = parse_interrupt_repr(candidate)
            if payload:
                return payload

    serialized_interrupt = make_json_serializable(raw_interrupt)
    if isinstance(serialized_interrupt, list):
        for entry in serialized_interrupt:
            if isinstance(entry, str):
                payload = parse_interrupt_repr(entry)
                if payload:
                    return payload

    return {"type": "approval_required", "value": serialized_interrupt}
