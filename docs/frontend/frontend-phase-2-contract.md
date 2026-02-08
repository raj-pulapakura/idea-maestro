# Idea Maestro Phase 2 Canonical Contract

Last updated: 2026-02-08 (Wave 3)

## API

### `POST /api/chat/{thread_id}`
Starts a new run for a user message.

Request:

```json
{
  "message": "string",
  "client_message_id": "optional-string"
}
```

Response: `text/event-stream` using the event contract below.

### `POST /api/chat/{thread_id}/approval`
Resumes workflow from `approval.required`.

Request:

```json
{
  "decision": "approve | reject | request_changes",
  "comment": "optional-string"
}
```

Response: `text/event-stream` using the same event contract.

### `GET /api/threads/{thread_id}/changesets`
Returns queue/history summary rows for a thread.

### `GET /api/threads/{thread_id}/changesets/{change_set_id}`
Returns changeset detail, including per-document before/after and review history.

### `GET /api/chat/{thread_id}`
Returns canonical thread snapshot for workspace hydration.

Response:

```json
{
  "ok": true,
  "thread_id": "string",
  "thread": {
    "thread_id": "string",
    "title": "string",
    "status": "active | archived",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "last_message_preview": "string | null"
  },
  "messages": [
    {
      "message_id": "string",
      "thread_id": "string",
      "run_id": "string | null",
      "seq": 1,
      "role": "user | assistant | tool | system",
      "type": "string | null",
      "content": {},
      "name": "string | null",
      "tool_call_id": "string | null",
      "tool_calls": "object | null",
      "metadata": {},
      "created_at": "ISO-8601",
      "by_agent": "string | null"
    }
  ],
  "docs": [
    {
      "thread_id": "string",
      "doc_id": "string",
      "title": "string",
      "content": "string",
      "description": "string",
      "version": 1,
      "updated_by": "string | null",
      "updated_at": "ISO-8601",
      "created_at": "ISO-8601"
    }
  ],
  "runs": [
    {
      "run_id": "string",
      "thread_id": "string",
      "trigger": "chat | approval",
      "status": "queued | running | waiting_approval | completed | error",
      "started_at": "ISO-8601",
      "completed_at": "ISO-8601 | null",
      "error": "string | null"
    }
  ],
  "agent_statuses": [
    {
      "run_id": "string",
      "thread_id": "string",
      "agent": "string",
      "status": "queued | thinking | tool_call | waiting_approval | done | error",
      "note": "string | null",
      "at": "ISO-8601"
    }
  ],
  "changesets": [
    {
      "change_set_id": "string",
      "thread_id": "string",
      "run_id": "string | null",
      "created_by": "string",
      "summary": "string",
      "status": "pending | approved | rejected | request_changes | applied",
      "created_at": "ISO-8601",
      "decided_at": "ISO-8601 | null",
      "decision_note": "string | null",
      "docs": ["doc_id"],
      "diffs": {
        "doc_id": "unified-diff"
      },
      "doc_changes": [
        {
          "doc_id": "string",
          "before_content": "string",
          "after_content": "string",
          "diff": "string"
        }
      ],
      "reviews": [
        {
          "decision": "approve | reject | request_changes",
          "comment": "string | null",
          "reviewed_by": "string | null",
          "reviewed_at": "ISO-8601 | null"
        }
      ]
    }
  ]
}
```

## Streaming Event Contract

All events include:

```json
{
  "event_id": "{run_id}:{sequence}",
  "thread_id": "string",
  "run_id": "string",
  "emitted_at": "ISO-8601"
}
```

Event types and payload extensions:

- `run.started`:
  - `status: "running"`
  - `trigger: "chat" | "approval"`
  - `started_at: ISO-8601`
- `agent.status`:
  - `agent: string`
  - `status: queued | thinking | tool_call | waiting_approval | done | error`
  - `note?: string`
  - `at: ISO-8601`
- `message.delta`:
  - `message_id: string`
  - `by_agent?: string`
  - `delta: string`
- `message.completed`:
  - `message_id: string`
  - `by_agent?: string`
  - `content: string`
- `tool.call`:
  - `message_id: string`
  - `by_agent?: string`
  - `tool_call: object`
- `tool.result`:
  - `message_id?: string`
  - `tool_name?: string`
  - `tool_call_id?: string`
  - `result: string | object`
- `keepalive`:
  - `status: "alive"`
  - `idle_seconds: number`
- `changeset.created | changeset.approved | changeset.rejected | changeset.request_changes | changeset.applied`
  - event-specific fields (minimum `change_set_id`)
- `approval.required`:
  - `type: "approval_required"`
  - `change_set: { change_set_id, summary, docs[], diffs{} }`
- `run.completed`:
  - `status: "completed" | "waiting_approval"`
  - `completed_at: ISO-8601`
- `run.error`:
  - `status: "error"`
  - `error: string`
  - `completed_at: ISO-8601`

Timeout semantics:
- Backend emits `keepalive` during idle graph periods.
- If no graph event is produced within timeout window, backend emits `run.error`.
- Client read path enforces inactivity timeout and surfaces retryable stream error.
