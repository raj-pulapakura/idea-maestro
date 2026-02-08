# Idea Maestro Frontend Implementation Tasks

Last updated: 2026-02-06  
Status legend: `[ ]` not started, `[~]` in progress, `[x]` done

## 1) Objective

Build the first usable UI slice that allows a user to:

1. Open the workspace UI with the target 3-column layout.
2. Send one chat message from the frontend.
3. Receive streamed backend events (agent text, tool activity, approval-required state).
4. Approve or reject one pending change set from the UI.

## 2) Phase Scope

## Core (Phase 1: must ship first)

- Desktop-first 3-column layout (sessions, chat, documents).
- Chat composer and send action wired to backend.
- Real streaming from backend (`/api/chat/{thread_id}`), not polling-only.
- Render streamed agent responses and tool activity in chat.
- Render approval-required card and allow approve/reject.
- Thread-aware flow (frontend uses a real `thread_id`, backend respects it).

## Nice-to-Have (Phase 2+)

- Full @mention dropdown and #doc mention dropdown.
- Session search and filtering logic.
- Document history tab, diff mode variants (inline vs side-by-side), review timeline.
- Pause/resume global orchestration behavior.
- Mobile/tablet adaptive drawers and tabs.

## 3) Assumptions and Constraints

- Backend currently has MVP orchestration and DB persistence.
- Backend endpoint currently contains temporary test artifacts and must be cleaned for UI use.
- For Phase 1, visual fidelity should match the mockup layout and hierarchy, not every micro-interaction.
- For Phase 1, single active session/thread is acceptable; multi-session management can be stubbed.

## 4) API Contract to Implement (Core)

### `POST /api/chat/{thread_id}` (streaming)

- Request body:
  - `message: string` (required)
  - `client_message_id: string` (optional)
- Response:
  - `text/event-stream` SSE with JSON payloads.
- Event types to support in Phase 1:
  - `thread.started`
  - `message.delta`
  - `message.completed`
  - `tool.call`
  - `tool.result`
  - `changeset.created`
  - `approval.required`
  - `run.completed`
  - `run.error`

### `POST /api/chat/{thread_id}/approval` (streaming resume)

- Request body:
  - `decision: "approve" | "reject"`
- Response:
  - SSE stream with same event envelope until next pause or completion.

### `GET /api/chat/{thread_id}`

- Returns persisted message history for initial hydration / refresh.

## 5) Structured Task Backlog

## Core Tasks

### `[x]` BE-01: Remove temporary route artifacts and accept real input

- Owner: Backend
- Depends on: none
- Files:
  - `backend/src/app/routes/chat.py`
- Implementation:
  - Stop overriding incoming `thread_id` with a new UUID.
  - Replace hardcoded `HumanMessage` body with request payload.
  - Add request model validation for `message`.
  - Preserve existing thread; only initialize docs for new thread.
- Done when:
  - Sending `POST /api/chat/{thread_id}` with different `thread_id` values results in separate persisted conversations.
  - Request body text appears in stored messages.
- Verification:
  - `curl` two different thread IDs, then `GET /api/chat/{thread_id}` for each and verify isolation.

### `[x]` BE-02: Stream graph events as SSE from chat endpoint

- Owner: Backend
- Depends on: `BE-01`
- Files:
  - `backend/src/app/routes/chat.py`
  - `backend/src/app/agents/helpers/emit_event.py` (event shape alignment if needed)
- Implementation:
  - Replace current non-streaming response with `StreamingResponse`.
  - Convert `graph.stream(...)` output into typed SSE events.
  - Emit events for message chunks/completion, custom tool/change-set events, approval interrupt boundary.
- Done when:
  - Browser/EventSource client receives incremental events before run completion.
  - Approval interrupt emits `approval.required` event instead of only server logs.
- Verification:
  - `curl -N` displays incremental `event:` and `data:` lines during one request.

### `[x]` BE-03: Stream resume after approval decision

- Owner: Backend
- Depends on: `BE-02`
- Files:
  - `backend/src/app/routes/chat.py`
- Implementation:
  - Make `/approval` endpoint stream resumed run events in SSE format.
  - Return terminal `run.completed` when no further interrupts occur.
- Done when:
  - Approve/reject from API resumes workflow and produces follow-up events.
- Verification:
  - Trigger approval-required state, call `/approval`, confirm resumed streamed messages/events.

### `[x]` BE-04: Fix change-set state field mismatch for safe apply

- Owner: Backend
- Depends on: none
- Files:
  - `backend/src/app/agents/nodes/change_set.py`
- Implementation:
  - Align `build_changeset_node` output keys with `apply_changeset_node` reads.
  - Ensure apply path uses `edits` and `summary` fields consistently.
- Done when:
  - Approving a change set updates docs without KeyError/missing-field issues.
- Verification:
  - Integration run with staged edits, approval, and DB doc update check.

### `[x]` FE-01: Build desktop 3-column app shell from design

- Owner: Frontend
- Depends on: none
- Files:
  - `frontend/app/page.tsx`
  - `frontend/app/globals.css`
  - optional extracted components under `frontend/app/components/*`
- Implementation:
  - Implement top app bar + left sessions column + center chat column + right docs column.
  - Match spacing, typography hierarchy, and color roles from `docs/frontend/code.html` and `docs/frontend/screen.png`.
  - Keep responsive collapse behavior minimal for Phase 1.
- Done when:
  - Layout visually matches reference structure at desktop width.
- Verification:
  - Manual QA screenshot comparison at 1440px width.

### `[~]` FE-02: Create chat state model and event reducer

- Owner: Frontend
- Depends on: `FE-01`, `BE-02` (event schema agreement)
- Files:
  - `frontend/app/*` (state module/hooks/components)
- Implementation:
  - Add strongly typed event model for SSE messages.
  - Build reducer/store for:
    - message list
    - tool events
    - pending approval card state
    - request lifecycle (idle/sending/streaming/error)
- Done when:
  - Incoming SSE events deterministically update UI state without ad-hoc parsing in components.
- Verification:
  - Unit tests for reducer transitions for `message.delta`, `message.completed`, and `approval.required`.

### `[x]` FE-03: Wire composer send to backend chat endpoint

- Owner: Frontend
- Depends on: `FE-02`, `BE-01`, `BE-02`
- Files:
  - `frontend/app/*` chat composer/client API modules
- Implementation:
  - Implement textarea composer + send button.
  - On send, call `POST /api/chat/{thread_id}` and open SSE stream reader.
  - Disable duplicate sends while active stream is in progress.
- Done when:
  - A user can type and submit one message and see streamed output arrive.
- Verification:
  - Manual end-to-end run from clean reload to first streamed response.

### `[x]` FE-04: Render streamed agent messages and tool activity

- Owner: Frontend
- Depends on: `FE-03`
- Files:
  - `frontend/app/*` message list components
- Implementation:
  - Render incremental message content while `message.delta` arrives.
  - Finalize message card on `message.completed`.
  - Render tool-call and tool-result activity tags/cards inline in timeline.
- Done when:
  - User sees progressive response and tool activity without page refresh.
- Verification:
  - Trigger request that uses at least one tool and confirm tool activity appears in UI.

### `[x]` FE-05: Minimal approval UI + decision actions

- Owner: Frontend
- Depends on: `FE-03`, `BE-03`
- Files:
  - `frontend/app/*` approval widget, client API actions
- Implementation:
  - Show approval card when `approval.required` event arrives (summary + doc list + optional diff preview text).
  - Add `Approve` and `Reject` buttons wired to `/api/chat/{thread_id}/approval`.
  - Continue rendering resumed stream after decision.
- Done when:
  - User can complete one approval loop fully from UI.
- Verification:
  - Manual scenario: stage edits -> approval required -> approve -> follow-up stream visible.

### `[x]` FE-06: Environment/config and failure handling

- Owner: Frontend
- Depends on: `FE-03`
- Files:
  - `frontend/.env` (or `.env.local`)
  - frontend API client modules
- Implementation:
  - Add configurable backend base URL.
  - Add clear inline states for network failure, stream parse error, and backend error event.
- Done when:
  - Misconfigured backend URL produces clear UI error and recoverable state.
- Verification:
  - Run once with invalid backend URL and verify user-visible failure state.

### `[~]` QA-01: Phase 1 E2E acceptance checklist

- Owner: Full stack
- Depends on: `BE-01..BE-04`, `FE-01..FE-06`
- Implementation:
  - Execute and record checklist:
    - Layout renders correctly.
    - Single message send works.
    - Streamed agent text appears incrementally.
    - Tool activity is visible.
    - Approval card appears.
    - Approve/reject path resumes stream.
    - Refresh can rehydrate thread from `GET /api/chat/{thread_id}`.
- Done when:
  - All checklist items are marked pass with evidence notes.
- Verification:
  - Store a short QA run log in this doc (date + pass/fail per item).

Current QA run log (2026-02-06):
- Pass: Frontend lint (`npm run lint`) succeeded.
- Pass: Frontend type-check (`npx tsc --noEmit`) succeeded.
- Pass: Frontend production build succeeded with webpack (`npx next build --webpack`).
- Pass: Backend syntax check succeeded (`PYTHONPYCACHEPREFIX=/tmp python3 -m py_compile ...`).
- Pending: Full live E2E with running backend model calls and approval interrupt round-trip in browser.

## Nice-to-Have Tasks

### `[ ]` FE-N1: @agent mention autocomplete and pills

- Owner: Frontend
- Depends on: `FE-03`
- Done when:
  - `@` opens keyboard-navigable agent picker; selected agents render as pills.

### `[ ]` FE-N2: #document mention autocomplete and pills

- Owner: Frontend
- Depends on: `FE-03`
- Done when:
  - `#` opens doc picker and inserts doc pills with stable IDs.

### `[ ]` FE-N3: Session list with search/filter and status chips

- Owner: Frontend
- Depends on: `FE-01`
- Done when:
  - Session panel supports filter chips and text search on mocked or real data.

### `[ ]` FE-N4: Right-panel document detail tabs (Current/History/Diffs)

- Owner: Frontend
- Depends on: `FE-01`, backend doc/history APIs
- Done when:
  - Document item opens detail tabs with usable content and version entries.

### `[ ]` FE-N5: Diff detail modes and review history timeline

- Owner: Frontend
- Depends on: `FE-N4`
- Done when:
  - User can toggle inline vs side-by-side diff view and inspect review history.

### `[ ]` FE-N6: Pause/Resume global loop controls wired to backend

- Owner: Full stack
- Depends on: backend pause/resume endpoints
- Done when:
  - Top-bar button reflects and controls orchestration pause state.

### `[ ]` FE-N7: Tablet/mobile adaptive navigation

- Owner: Frontend
- Depends on: `FE-01`
- Done when:
  - Left/right panes collapse into drawers or tabbed navigation on small screens.

## 6) Delivery Sequence (Recommended)

1. `BE-01`, `BE-04`  
2. `BE-02`, `BE-03`  
3. `FE-01`, `FE-02`  
4. `FE-03`, `FE-04`, `FE-05`  
5. `FE-06`, `QA-01`  
6. Nice-to-have tasks

## 7) Explicit Out of Scope for Phase 1

- Full production-grade auth and user profiles.
- Multi-workspace persistence and advanced session management.
- Complete document authoring/editing suite.
- Final visual polish for all micro-interactions and animations.
