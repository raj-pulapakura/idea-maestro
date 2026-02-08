from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Empty, Queue
from threading import Thread
from time import monotonic
from typing import Any, Iterator, Optional

from app.db.run_repository import append_agent_status, set_run_status
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

HEARTBEAT_INTERVAL_SECONDS = 8.0
STREAM_TIMEOUT_SECONDS = 45.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@dataclass
class StreamEmitter:
    thread_id: str
    run_id: str
    _seq: int = 0

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        self._seq += 1
        base_payload = {
            "event_id": f"{self.run_id}:{self._seq}",
            "thread_id": self.thread_id,
            "run_id": self.run_id,
            "emitted_at": _now_iso(),
        }
        base_payload.update(payload)
        return to_sse(event_type, base_payload)


def _graph_stream_worker(
    *,
    graph: Any,
    graph_input: dict[str, Any] | Any,
    config: dict[str, Any],
    out_queue: Queue[tuple[str, Any]],
) -> None:
    try:
        for item in graph.stream(
            graph_input,
            stream_mode=["messages", "updates", "custom"],
            config=config,
            subgraphs=True,
        ):
            out_queue.put(("record", item))
    except Exception as exc:
        out_queue.put(("error", exc))
    finally:
        out_queue.put(("done", None))


def stream_graph_events(
    *,
    graph_input: dict[str, Any] | Any,
    config: dict[str, Any],
    thread_id: str,
    run_id: str,
    trigger: str,
    graph: Any,
) -> Iterator[str]:
    emitter = StreamEmitter(thread_id=thread_id, run_id=run_id)

    message_buffers: dict[str, dict[str, Any]] = {}
    completed_ids: set[str] = set()
    fallback_message_id: Optional[str] = None
    emitted_tool_calls: set[str] = set()
    active_agent: str | None = None
    last_agent_status: dict[str, str] = {}
    interrupted_for_approval = False

    def emit_agent_status(
        agent: str,
        status: str,
        *,
        note: str | None = None,
        force: bool = False,
    ) -> str | None:
        if not force and last_agent_status.get(agent) == status:
            return None

        last_agent_status[agent] = status
        persisted = append_agent_status(
            run_id=run_id,
            thread_id=thread_id,
            agent=agent,
            status=status,
            note=note,
        )
        return emitter.emit("agent.status", persisted)

    set_run_status(run_id, status="running")
    run_started_at = _now_iso()
    yield emitter.emit(
        "run.started",
        {
            "status": "running",
            "trigger": trigger,
            "started_at": run_started_at,
        },
    )

    maestro_status = emit_agent_status("maestro", "queued", note="run initialized", force=True)
    if maestro_status:
        yield maestro_status

    queue: Queue[tuple[str, Any]] = Queue()
    worker = Thread(
        target=_graph_stream_worker,
        kwargs={
            "graph": graph,
            "graph_input": graph_input,
            "config": config,
            "out_queue": queue,
        },
        daemon=True,
    )
    worker.start()

    last_graph_activity = monotonic()

    try:
        stream_done = False

        while not stream_done:
            try:
                item_type, item_payload = queue.get(timeout=HEARTBEAT_INTERVAL_SECONDS)
            except Empty:
                idle_seconds = monotonic() - last_graph_activity
                if idle_seconds >= STREAM_TIMEOUT_SECONDS:
                    raise TimeoutError(
                        f"No graph events for {int(STREAM_TIMEOUT_SECONDS)} seconds"
                    )
                yield emitter.emit(
                    "keepalive",
                    {
                        "status": "alive",
                        "idle_seconds": int(idle_seconds),
                    },
                )
                continue

            if item_type == "done":
                stream_done = True
                continue

            if item_type == "error":
                raise item_payload

            if item_type != "record":
                continue

            last_graph_activity = monotonic()
            namespace, mode, data = item_payload
            by_agent = guess_agent_from_namespace(namespace)

            if by_agent:
                if active_agent and by_agent != active_agent:
                    finished_status = emit_agent_status(active_agent, "done")
                    if finished_status:
                        yield finished_status
                active_agent = by_agent
                thinking_status = emit_agent_status(by_agent, "thinking")
                if thinking_status:
                    yield thinking_status

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

                        yield emitter.emit(
                            "message.delta",
                            {
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
                        yield emitter.emit(
                            "tool.call",
                            {
                                "message_id": msg_id,
                                "by_agent": by_agent,
                                "tool_call": tool_call,
                            },
                        )
                        if by_agent:
                            tool_status = emit_agent_status(by_agent, "tool_call")
                            if tool_status:
                                yield tool_status

                    for tool_call in normalize_tool_calls(
                        getattr(msg, "tool_call_chunks", None)
                    ):
                        tool_key = json.dumps(tool_call, sort_keys=True, default=str)
                        if tool_key in emitted_tool_calls:
                            continue
                        emitted_tool_calls.add(tool_key)
                        yield emitter.emit(
                            "tool.call",
                            {
                                "message_id": msg_id,
                                "by_agent": by_agent,
                                "tool_call": tool_call,
                            },
                        )
                        if by_agent:
                            tool_status = emit_agent_status(by_agent, "tool_call")
                            if tool_status:
                                yield tool_status

                    response_metadata = getattr(msg, "response_metadata", {}) or {}
                    finish_reason = response_metadata.get("finish_reason")
                    if finish_reason and msg_id not in completed_ids:
                        buffered = message_buffers.get(msg_id, {})
                        yield emitter.emit(
                            "message.completed",
                            {
                                "message_id": msg_id,
                                "by_agent": buffered.get("by_agent", by_agent),
                                "content": buffered.get("content", ""),
                            },
                        )
                        completed_ids.add(msg_id)
                        if fallback_message_id == msg_id:
                            fallback_message_id = None

                elif msg_role == "tool":
                    yield emitter.emit(
                        "tool.result",
                        {
                            "message_id": getattr(msg, "id", str(uuid.uuid4())),
                            "tool_name": getattr(msg, "name", None),
                            "tool_call_id": getattr(msg, "tool_call_id", None),
                            "result": extract_text(getattr(msg, "content", None)),
                        },
                    )

            elif mode == "custom":
                event_payload = (
                    data if isinstance(data, dict) else {"value": make_json_serializable(data)}
                )
                event_type = event_payload.get("type", "custom")

                if event_type == "agent.staged_edits":
                    yield emitter.emit(
                        "tool.result",
                        {
                            "tool_name": "stage_edits",
                            "result": event_payload,
                        },
                    )
                elif isinstance(event_type, str) and event_type.startswith("changeset."):
                    yield emitter.emit(event_type, event_payload)
                else:
                    yield emitter.emit("custom", event_payload)

            elif mode == "updates":
                if isinstance(data, dict):
                    approval = find_approval_interrupt(data)
                    if approval:
                        interrupted_for_approval = True
                        if active_agent:
                            waiting_status = emit_agent_status(active_agent, "waiting_approval")
                            if waiting_status:
                                yield waiting_status
                        set_run_status(run_id, status="waiting_approval", completed=True)
                        yield emitter.emit("approval.required", approval)
                        break

        for message_id, buffered in message_buffers.items():
            if message_id in completed_ids:
                continue
            if not buffered.get("content"):
                continue

            yield emitter.emit(
                "message.completed",
                {
                    "message_id": message_id,
                    "by_agent": buffered.get("by_agent"),
                    "content": buffered.get("content", ""),
                },
            )

        if interrupted_for_approval:
            yield emitter.emit(
                "run.completed",
                {
                    "status": "waiting_approval",
                    "completed_at": _now_iso(),
                },
            )
            return

        if active_agent:
            done_status = emit_agent_status(active_agent, "done")
            if done_status:
                yield done_status

        set_run_status(run_id, status="completed", completed=True)
        yield emitter.emit(
            "run.completed",
            {
                "status": "completed",
                "completed_at": _now_iso(),
            },
        )
    except Exception as exc:
        if active_agent:
            error_status = emit_agent_status(active_agent, "error", note=str(exc), force=True)
            if error_status:
                yield error_status

        set_run_status(run_id, status="error", error=str(exc), completed=True)
        yield emitter.emit(
            "run.error",
            {
                "status": "error",
                "error": str(exc),
                "completed_at": _now_iso(),
            },
        )
