from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import psycopg

DEFAULT_THREAD_TITLE = "Untitled Thread"
MAX_AUTO_TITLE_LENGTH = 72


def _extract_preview(message: Dict[str, Any]) -> str | None:
    content = message.get("content")
    if not isinstance(content, dict):
        return None

    text_value = content.get("text")
    if isinstance(text_value, str) and text_value.strip():
        return text_value.strip()[:160]

    blocks = content.get("blocks")
    if not isinstance(blocks, list):
        return None

    parts: list[str] = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(block)
            continue
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])

    joined = "".join(parts).strip()
    return joined[:160] if joined else None


def _derive_auto_title(messages: List[Dict[str, Any]]) -> str | None:
    for message in messages:
        if message.get("role") != "user":
            continue
        preview = _extract_preview(message)
        if not preview:
            continue
        normalized = " ".join(preview.split())
        return normalized[:MAX_AUTO_TITLE_LENGTH]
    return None


def persist_messages_to_db(
    conn: psycopg.Connection,
    thread_id: str,
    messages: List[Dict[str, Any]],
    *,
    run_id: str | None = None,
) -> Tuple[int, int]:
    if not messages:
        raise ValueError("messages is empty")

    n = len(messages)

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_threads(thread_id)
                VALUES (%s)
                ON CONFLICT (thread_id) DO NOTHING
                """,
                (thread_id,),
            )

            cur.execute(
                """
                UPDATE chat_threads
                SET next_seq = next_seq + %s
                WHERE thread_id = %s
                RETURNING next_seq - %s
                """,
                (n, thread_id, n),
            )
            start_seq = cur.fetchone()[0]

            rows = []
            for i, m in enumerate(messages):
                seq = start_seq + i
                rows.append(
                    (
                        m.get("message_id") or f"{thread_id}:{seq}",
                        thread_id,
                        run_id,
                        seq,
                        m["role"],
                        m.get("type"),
                        json.dumps(m["content"]),
                        m.get("name"),
                        m.get("tool_call_id"),
                        json.dumps(m.get("tool_calls"))
                        if m.get("tool_calls") is not None
                        else None,
                        json.dumps(m.get("metadata", {})),
                        m.get("by_agent"),
                    )
                )

            cur.executemany(
                """
                INSERT INTO chat_messages (
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
                  by_agent
                ) VALUES (
                  %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  %s::jsonb,
                  %s,
                  %s,
                  %s::jsonb,
                  %s::jsonb,
                  %s
                )
                """,
                rows,
            )

            preview = _extract_preview(messages[-1])
            cur.execute(
                """
                UPDATE chat_threads
                SET
                  updated_at = NOW(),
                  last_message_preview = COALESCE(%s, last_message_preview)
                WHERE thread_id = %s
                """,
                (preview, thread_id),
            )

            auto_title = _derive_auto_title(messages)
            if start_seq == 1 and auto_title:
                cur.execute(
                    """
                    UPDATE chat_threads
                    SET title = %s
                    WHERE thread_id = %s
                      AND (title IS NULL OR BTRIM(title) = '' OR title = %s)
                    """,
                    (auto_title, thread_id, DEFAULT_THREAD_TITLE),
                )

    end_seq = start_seq + n - 1
    return start_seq, end_seq
