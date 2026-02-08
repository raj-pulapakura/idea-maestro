import json
import uuid
from typing import Any, Iterator, Optional

from .serialization import (
    extract_text,
    find_approval_interrupt,
    guess_agent_from_namespace,
    make_json_serializable,
    normalize_tool_calls,
)


STREAM_RESPONSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def to_sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_graph_events(
    *,
    graph_input: dict[str, Any] | Any,
    config: dict[str, Any],
    thread_id: str,
    graph: Any,
    emit_thread_started: bool,
) -> Iterator[str]:
    message_buffers: dict[str, dict[str, Any]] = {}
    completed_ids: set[str] = set()
    fallback_message_id: Optional[str] = None
    emitted_tool_calls: set[str] = set()

    if emit_thread_started:
        yield to_sse("thread.started", {"thread_id": thread_id})

    try:
        for namespace, mode, data in graph.stream(
            graph_input,
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True,
        ):
            by_agent = guess_agent_from_namespace(namespace)

            if mode == "messages":
                msg, _ = data
                msg_role = getattr(msg, "type", None)

                if msg_role == "ai":
                    msg_id = getattr(msg, "id", None)
                    if not msg_id:
                        if fallback_message_id is None:
                            fallback_message_id = str(uuid.uuid4())
                        msg_id = fallback_message_id
                    else:
                        fallback_message_id = msg_id

                    text_delta = extract_text(getattr(msg, "content", None))
                    if text_delta:
                        existing = message_buffers.setdefault(
                            msg_id,
                            {"content": "", "by_agent": by_agent},
                        )
                        existing["content"] += text_delta
                        if by_agent:
                            existing["by_agent"] = by_agent

                        yield to_sse(
                            "message.delta",
                            {
                                "thread_id": thread_id,
                                "message_id": msg_id,
                                "by_agent": existing.get("by_agent"),
                                "delta": text_delta,
                            },
                        )

                    for tool_call in normalize_tool_calls(getattr(msg, "tool_calls", None)):
                        tool_key = json.dumps(tool_call, sort_keys=True, default=str)
                        if tool_key in emitted_tool_calls:
                            continue
                        emitted_tool_calls.add(tool_key)
                        yield to_sse(
                            "tool.call",
                            {
                                "thread_id": thread_id,
                                "message_id": msg_id,
                                "by_agent": by_agent,
                                "tool_call": tool_call,
                            },
                        )

                    for tool_call in normalize_tool_calls(
                        getattr(msg, "tool_call_chunks", None)
                    ):
                        tool_key = json.dumps(tool_call, sort_keys=True, default=str)
                        if tool_key in emitted_tool_calls:
                            continue
                        emitted_tool_calls.add(tool_key)
                        yield to_sse(
                            "tool.call",
                            {
                                "thread_id": thread_id,
                                "message_id": msg_id,
                                "by_agent": by_agent,
                                "tool_call": tool_call,
                            },
                        )

                    response_metadata = getattr(msg, "response_metadata", {}) or {}
                    finish_reason = response_metadata.get("finish_reason")
                    if finish_reason and msg_id not in completed_ids:
                        buffered = message_buffers.get(msg_id, {})
                        yield to_sse(
                            "message.completed",
                            {
                                "thread_id": thread_id,
                                "message_id": msg_id,
                                "by_agent": buffered.get("by_agent", by_agent),
                                "content": buffered.get("content", ""),
                            },
                        )
                        completed_ids.add(msg_id)
                        if fallback_message_id == msg_id:
                            fallback_message_id = None

                elif msg_role == "tool":
                    tool_payload = {
                        "thread_id": thread_id,
                        "message_id": getattr(msg, "id", str(uuid.uuid4())),
                        "tool_name": getattr(msg, "name", None),
                        "tool_call_id": getattr(msg, "tool_call_id", None),
                        "result": extract_text(getattr(msg, "content", None)),
                    }
                    yield to_sse("tool.result", tool_payload)

            elif mode == "custom":
                event_payload = (
                    data if isinstance(data, dict) else {"value": make_json_serializable(data)}
                )
                event_type = event_payload.get("type", "custom")

                if event_type == "agent.staged_edits":
                    yield to_sse(
                        "tool.result",
                        {
                            "thread_id": thread_id,
                            "tool_name": "stage_edits",
                            "result": event_payload,
                        },
                    )
                elif event_type == "changeset.created":
                    yield to_sse("changeset.created", {"thread_id": thread_id, **event_payload})
                elif event_type.startswith("changeset."):
                    yield to_sse(event_type, {"thread_id": thread_id, **event_payload})
                else:
                    yield to_sse("custom", {"thread_id": thread_id, **event_payload})

            elif mode == "updates":
                serializable_updates = make_json_serializable(data)
                if isinstance(serializable_updates, dict):
                    approval = find_approval_interrupt(serializable_updates)
                    if approval:
                        yield to_sse("approval.required", {"thread_id": thread_id, **approval})
                        break

        for message_id, buffered in message_buffers.items():
            if message_id in completed_ids:
                continue
            if not buffered.get("content"):
                continue

            yield to_sse(
                "message.completed",
                {
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "by_agent": buffered.get("by_agent"),
                    "content": buffered.get("content", ""),
                },
            )

        yield to_sse("run.completed", {"thread_id": thread_id})
    except Exception as exc:
        yield to_sse("run.error", {"thread_id": thread_id, "error": str(exc)})
