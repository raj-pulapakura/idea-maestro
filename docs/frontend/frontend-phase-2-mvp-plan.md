# Idea Maestro Phase 2 Plan (MVP-Ready)

Last updated: 2026-02-08  
Status legend: `[ ]` not started, `[~]` in progress, `[x]` done  
Primary goal: move from "demo-capable Phase 1" to "usable MVP with real data, multi-thread workflows, reliable streaming UX, and actionable diff review."

## 1) Product Context

Phase 1 validated:

- 3-column app shell and chat composer.
- Backend streaming path (`/api/chat/{thread_id}` + `/approval`).
- Basic approval card and action wiring.

Phase 2 must deliver:

- Real, non-dummy session and document data.
- Multi-thread workflow users can trust.
- Streaming UX that clearly shows progress in real time.
- Open/read living docs with version and change provenance.
- A usable diff/review interface (guided by `docs/frontend/diff/code.html` and `docs/frontend/diff/screen.png`).

## 2) Current State Audit (Gaps)

## Frontend gaps

- `SessionsPanel` still renders static sample sessions (no API data).
- `DocumentsPanel` still renders static sample docs (no API data).
- Thread selection/creation UX is not implemented; single localStorage thread is used.
- Message streaming is shown, but no explicit run timeline or agent "working" states.
- Approval UI is minimal and not tied to a full diff review surface.
- No dedicated doc reader/detail panel for full living document content.
- No route-level thread URL (`/threads/{id}`) for deep-linking/reload clarity.

## Backend/API gaps

- No thread list/create endpoints for session navigation.
- No docs read endpoints for right-panel living documents.
- No persisted change-set history API for review timelines.
- Docs persistence is SCD1 overwrite only; no version history table yet.
- Event stream does not emit full run/agent lifecycle states needed for status chips.
- Approval endpoint supports only approve/reject; no "request changes" path yet.

## Data-model gaps

- `chat_threads` has only sequencing metadata; lacks title/status/updated-at/user-facing fields.
- `docs` table lacks explicit version rows/history metadata.
- No durable tables for `changesets` and review decisions (approved/rejected/requested-changes).

## 3) Constraints and Guardrails

- Clean-slate refactor is allowed for Phase 2:
  breaking API/schema/UI changes are acceptable.
- Protocol churn is acceptable during Phase 2 implementation:
  optimize for speed and correctness over backwards compatibility.
- DB migrations do not need to be additive-only:
  destructive/rebuild migrations are acceptable in current stage.
- Preserve chat responsiveness:
  streaming UI must remain incremental and non-blocking.
- Phase 2 still targets MVP scope:
  no full auth/multi-tenant hardening unless needed for correctness.

## 4) Phase 2 Scope Definition

## In scope (must ship for Phase 2)

- Real sessions/threads list with create + select + reload.
- Real living documents list + open/read detail.
- Agent run statuses in UI (routing/working/waiting approval/done).
- Diff review interface with before/after and approval actions.
- Persisted review history per change-set.
- Stream fidelity improvements (order guarantees, stable IDs, explicit lifecycle events).

## Out of scope (defer to Phase 3)

- Full collaborative multi-user editing.
- Production auth and org-level permissions.
- Mobile-first redesign (basic responsiveness only).
- Advanced analytics dashboards.

## 5) Proposed Architecture (Phase 2)

## Backend route modules

- Keep `routes/chat/*` as streaming core.
- Add `routes/threads/*` for session management.
- Add `routes/docs/*` for living docs read endpoints.
- Add `routes/reviews/*` for change-set/diff review retrieval and decisions.

## Stream Contract (Phase 2)

Add these events (or equivalent fields) on top of Phase 1:

- `run.started` `{run_id, thread_id, started_at}`
- `agent.status` `{run_id, agent, status, note?}` where status is:
  `queued | thinking | tool_call | waiting_approval | done | error`
- `message.delta` `{run_id, message_id, ...}`
- `message.completed` `{run_id, message_id, ...}`
- `tool.call` / `tool.result`
- `changeset.created` `{change_set_id, doc_ids, summary, created_by}`
- `approval.required` `{change_set}`
- `changeset.approved` / `changeset.rejected` / `changeset.applied`
- `run.completed` / `run.error`

## Data model additions (proposed)

- Extend `chat_threads`:
  `title`, `status`, `created_at`, `updated_at`, `last_message_preview`.
- Add `doc_versions`:
  immutable rows per doc change (`thread_id`, `doc_id`, `version`, `content`, `summary`, `updated_by`, `created_at`, `change_set_id`).
- Add `change_sets`:
  `change_set_id`, `thread_id`, `created_by`, `summary`, `status`, `created_at`.
- Add `change_set_docs`:
  per-doc diff payload or diff reference.
- Add `change_set_reviews`:
  `change_set_id`, `decision`, `comment`, `reviewed_at`, optional `reviewed_by`.

## Frontend feature modules

- Keep current `features/workspace/*` split.
- Add:
  `features/threads/*`, `features/documents/*`, `features/review/*`, `features/agents/*`.
- Move from localStorage-only thread to URL + store synchronized thread context.

## 6) Detailed Task Backlog

## Workstream A: Backend Foundation and APIs

### `[x]` P2-BE-00: Reset schema and finalize canonical Phase 2 contracts

- Owner: Backend
- Depends on: none
- Includes:
  - Define final Phase 2 API payloads/events (single canonical contract).
  - Implement DB reset migration(s) for MVP-stage clean slate.
  - Remove/replace legacy tables/columns not needed by Phase 2 shape.
- Acceptance:
  - One documented contract and one canonical DB schema are active.
  - Backend boots from fresh DB with no compatibility shims.
- Verification:
  - Cold-start integration test on empty DB and fresh migration run.
- Wave 0 implementation notes:
  - Canonical schema reset migration added: `backend/src/app/db/migrations/0001_phase2_reset.sql`.
  - Migration runner wired at startup: `backend/src/app/db/migrations.py` + `backend/src/app/main.py`.
  - Canonical contract doc added: `docs/frontend/frontend-phase-2-contract.md`.

### `[x]` P2-BE-01: Add thread list/create/update endpoints

- Owner: Backend
- Depends on: `P2-BE-00`
- Files:
  - `backend/src/app/routes/threads/*` (new)
  - DB helpers under `backend/src/app/db/*` (new)
- API:
  - `GET /api/threads`
  - `POST /api/threads`
  - `PATCH /api/threads/{thread_id}`
- Acceptance:
  - Frontend can create and retrieve multiple threads with metadata.
- Verification:
  - API tests for pagination/order/create/update title/status.
- Wave 1 implementation notes:
  - Added `GET /api/threads`, `POST /api/threads`, `PATCH /api/threads/{thread_id}`.
  - Files: `backend/src/app/routes/threads/router.py`, `backend/src/app/routes/threads/models.py`, `backend/src/app/db/thread_repository.py`.

### `[x]` P2-BE-02: Add docs read endpoints for living docs panel

- Owner: Backend
- Depends on: `P2-BE-00`, `P2-BE-01`
- API:
  - `GET /api/threads/{thread_id}/docs`
  - `GET /api/threads/{thread_id}/docs/{doc_id}`
- Acceptance:
  - Documents panel can render real docs and open full content view.
- Verification:
  - API test returns persisted docs for both new and existing threads.
- Wave 1 implementation notes:
  - Added `GET /api/threads/{thread_id}/docs` and `GET /api/threads/{thread_id}/docs/{doc_id}`.
  - Files: `backend/src/app/routes/docs/router.py`, `backend/src/app/db/fetch_thread_docs.py`.

### `[x]` P2-BE-03: Introduce persistent change-set and review history tables

- Owner: Backend
- Depends on: `P2-BE-00`
- Includes:
  - DB migration scripts for `change_sets`, `change_set_docs`, `change_set_reviews`, optionally `doc_versions`.
- Acceptance:
  - Every approval flow persists a retrievable review record.
- Verification:
  - Integration test: create changeset -> approve/reject -> query history endpoint.
- Wave 2 implementation notes:
  - Persisted `change_sets`, `change_set_docs`, `change_set_reviews`, and `doc_versions` are active in canonical schema.
  - Changeset create/status/review persistence wired in `backend/src/app/db/changeset_repository.py` and `backend/src/app/agents/nodes/change_set.py`.

### `[x]` P2-BE-04: Add review/diff retrieval endpoints

- Owner: Backend
- Depends on: `P2-BE-03`
- API:
  - `GET /api/threads/{thread_id}/changesets`
  - `GET /api/threads/{thread_id}/changesets/{change_set_id}`
- Acceptance:
  - Frontend can load a change queue and open a selected diff detail view.
- Verification:
  - Endpoint contract tests with deterministic fixture diffs.
- Wave 2 implementation notes:
  - Added `GET /api/threads/{thread_id}/changesets` and `GET /api/threads/{thread_id}/changesets/{change_set_id}`.
  - Detail payload includes `doc_changes` (before/after/diff) and `reviews` history.
  - Files: `backend/src/app/routes/reviews/router.py`, `backend/src/app/db/changeset_repository.py`.

### `[x]` P2-BE-05: Upgrade approval endpoint to include request-changes

- Owner: Backend
- Depends on: `P2-BE-03`, `P2-BE-04`
- API:
  - `POST /api/chat/{thread_id}/approval` with decision:
    `approve | reject | request_changes` and optional comment.
- Acceptance:
  - Request-changes decision is stored and surfaced in review history.
- Verification:
  - End-to-end approval decision matrix test.
- Wave 2 implementation notes:
  - `/api/chat/{thread_id}/approval` now accepts `approve | reject | request_changes` plus optional `comment`.
  - Decision + comment are persisted into review history rows.
  - Files: `backend/src/app/routes/chat/models.py`, `backend/src/app/routes/chat/router.py`, `backend/src/app/agents/nodes/change_set.py`.

### `[x]` P2-BE-06: Finalize Phase 2 stream contract for agent statuses and run lifecycle

- Owner: Backend
- Depends on: `P2-BE-00`
- Includes:
  - Add `run_id` and lifecycle events.
  - Emit `agent.status` transitions consistently.
- Acceptance:
  - Frontend can show real-time run state and per-agent activity without inference hacks.
- Verification:
  - Stream fixture test asserting event order and required fields.
- Wave 0 implementation notes:
  - Stream now emits canonical lifecycle events with `event_id`, `run_id`, and `emitted_at`.
  - `run.started` / `run.completed` / `run.error` and `agent.status` transitions are emitted and persisted.
  - Run + agent status persistence added under `backend/src/app/db/run_repository.py`.

### `[x]` P2-BE-07: Thread bootstrapping correctness for non-empty threads

- Owner: Backend
- Depends on: `P2-BE-00`, `P2-BE-01`
- Includes:
  - Avoid false "new thread" detection via message existence only.
  - Use thread table existence/metadata source of truth.
- Acceptance:
  - Existing threads never reinitialize docs or reset run context.
- Verification:
  - Regression tests with threads containing docs but sparse messages.
- Wave 1 implementation notes:
  - Added `chat_threads.docs_initialized` metadata and bootstrap guards.
  - Docs initialization now keys off thread metadata, not message history.
  - Files: `backend/src/app/db/migrations/0001_phase2_reset.sql`, `backend/src/app/routes/chat/service.py`, `backend/src/app/db/thread_repository.py`.

## Workstream B: Frontend Threading and Real Data

### `[x]` P2-FE-00: Refactor workspace state for canonical Phase 2 data model

- Owner: Frontend
- Depends on: `P2-BE-00`, `P2-BE-06`
- Includes:
  - Replace Phase 1 stream assumptions with final event/state model.
  - Introduce explicit entities in state:
    `threads`, `activeThreadId`, `docs`, `runs`, `agentStatuses`, `changesets`.
- Acceptance:
  - Store shape mirrors backend contracts; no compatibility adapters remain.
- Verification:
  - Reducer test suite covers full Phase 2 event set.
- Wave 0 implementation notes:
  - Workspace store refactored to canonical entities: `threads`, `activeThreadId`, `docs`, `runs`, `agentStatuses`, `changesets`.
  - Stream handling updated to finalized lifecycle/status contract and snapshot hydration model.
  - Files updated: `frontend/app/features/workspace/state/types.ts`, `frontend/app/features/workspace/state/reducer.ts`, `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`.

### `[x]` P2-FE-01: Replace static sessions panel with real thread data

- Owner: Frontend
- Depends on: `P2-FE-00`, `P2-BE-01`
- Includes:
  - Threads fetch/create/select.
  - Loading/empty/error states.
- Acceptance:
  - User can create/select threads and see chat/doc context switch correctly.
- Verification:
  - Manual scenario test with 3+ threads and persistence across reload.
- Wave 1 implementation notes:
  - Sessions panel now renders API-backed threads with create/select behavior.
  - Files: `frontend/app/features/workspace/components/SessionsPanel.tsx`, `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/features/workspace/api/chat-client.ts`.

### `[x]` P2-FE-02: Add route-driven thread context

- Owner: Frontend
- Depends on: `P2-FE-00`, `P2-FE-01`
- Includes:
  - Use route segment/query (`/workspace?thread=...` or `/threads/[threadId]`).
  - Sync selection with URL.
- Acceptance:
  - Deep-link opens exact thread and hydrates chat/docs.
- Verification:
  - Hard refresh on specific URL preserves current thread context.
- Wave 1 implementation notes:
  - Implemented `?thread={thread_id}` URL synchronization with selection and bootstrap.
  - Files: `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/page.tsx`.

### `[x]` P2-FE-03: Replace static documents panel with API-backed list

- Owner: Frontend
- Depends on: `P2-FE-00`, `P2-BE-02`, `P2-FE-01`
- Acceptance:
  - Right panel shows thread-scoped real docs and metadata.
- Verification:
  - Switch thread -> docs list changes accordingly.
- Wave 1 implementation notes:
  - Documents panel now loads thread-scoped docs via docs API endpoints.
  - Files: `frontend/app/features/workspace/components/DocumentsPanel.tsx`, `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/features/workspace/api/chat-client.ts`.

### `[x]` P2-FE-04: Add document reader detail view (open/read)

- Owner: Frontend
- Depends on: `P2-FE-02`, `P2-FE-03`
- Includes:
  - Current document view with content, summary, updated-by, updated-at.
- Acceptance:
  - Clicking a document opens a readable detail pane.
- Verification:
  - Doc content matches backend response for selected thread/doc.
- Wave 1 implementation notes:
  - Added active document reader pane with metadata + full content.
  - Detail refresh wired through `GET /api/threads/{thread_id}/docs/{doc_id}`.

### `[x]` P2-FE-05: Real stream lifecycle handling with run/agent statuses

- Owner: Frontend
- Depends on: `P2-FE-00`, `P2-BE-06`
- Includes:
  - Render status chips and "working/thinking" indicators per agent.
  - Track run-level progress.
- Acceptance:
  - User can see which agent is active and when run is waiting on approval.
- Verification:
  - Stream simulation test for lifecycle transitions.
- Wave 3 implementation notes:
  - Added run status + per-agent status chips in chat and review workspace headers.
  - Statuses are sourced directly from canonical `runs` + `agentStatuses` entities.
  - Files: `frontend/app/features/workspace/components/ChatPanel.tsx`, `frontend/app/features/workspace/components/ReviewWorkspace.tsx`, `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`.

## Workstream C: Diff and Review Experience

### `[x]` P2-FE-06: Add review workspace shell using diff reference

- Owner: Frontend
- Depends on: `P2-FE-02`, `P2-FE-03`, `P2-BE-04`
- Reference:
  - `docs/frontend/diff/code.html`
  - `docs/frontend/diff/screen.png`
- Includes:
  - Diff mode panel split:
    project feed + before/after viewer + approval action row.
- Acceptance:
  - User can enter review mode from pending changes and inspect diffs.
- Verification:
  - Visual parity check against reference for core elements (not exact clone).
- Wave 2 implementation notes:
  - Added review workspace mode with project feed + diff workspace + sticky decision bar.
  - Files: `frontend/app/features/workspace/components/ReviewWorkspace.tsx`, `frontend/app/features/workspace/WorkspaceScreen.tsx`.

### `[x]` P2-FE-07: Implement unified and side-by-side diff viewers

- Owner: Frontend
- Depends on: `P2-FE-06`
- Acceptance:
  - Toggle between two diff modes with stable scroll and syntax highlighting.
- Verification:
  - Snapshot tests with known diff fixtures.
- Wave 2 implementation notes:
  - Added toggle between side-by-side before/after and unified diff rendering in review workspace.

### `[x]` P2-FE-08: Add change queue and review history timeline

- Owner: Frontend
- Depends on: `P2-FE-06`, `P2-BE-04`, `P2-BE-05`
- Acceptance:
  - Queue shows pending/resolved reviews; selecting item loads detail.
- Verification:
  - Multi-change-set scenario test with mixed decisions.
- Wave 2 implementation notes:
  - Added thread-scoped changeset queue with selection and persisted review history list.
  - Hook/API integration: `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/features/workspace/api/chat-client.ts`.

### `[x]` P2-FE-09: Complete approval action bar

- Owner: Frontend
- Depends on: `P2-FE-07`, `P2-FE-08`, `P2-BE-05`
- Includes:
  - Approve / Reject / Request Changes + optional comment.
- Acceptance:
  - Decision updates stream + history + queue status.
- Verification:
  - End-to-end interaction test for all decision types.
- Wave 2 implementation notes:
  - Added action bar with Approve / Reject / Request Changes and optional review comment.
  - Decisions flow through stream + backend persistence and refresh selected changeset detail.

## Workstream D: Reliability and UX Quality

### `[x]` P2-FE-10: Harden streaming parser and UI ordering guarantees

- Owner: Frontend
- Depends on: `P2-FE-00`, `P2-BE-06`
- Includes:
  - Deterministic ordering by `run_id` + message/event IDs.
  - Handling duplicate or late completion events.
- Acceptance:
  - No duplicate message bubbles during long streams.
- Verification:
  - Reducer tests with out-of-order/duplicate stream fixtures.
- Wave 3 implementation notes:
  - Added reducer-level event dedup using `event_id`.
  - Added per-message completion guards to ignore late duplicate deltas.
  - Timeline ordering now uses deterministic tie-break (`createdAt` then ID).
  - Client stream reader now enforces inactivity timeout for actionable retry errors.
  - Files: `frontend/app/features/workspace/state/reducer.ts`, `frontend/app/features/workspace/state/types.ts`, `frontend/app/features/workspace/utils/timeline.ts`, `frontend/app/features/workspace/api/chat-client.ts`.

### `[x]` P2-BE-08: Add stream keepalive/timeout behavior

- Owner: Backend
- Depends on: `P2-BE-06`
- Includes:
  - Keepalive comments or heartbeat events.
  - Explicit timeout/error semantics.
- Acceptance:
  - Client can detect dead streams quickly and show actionable retry.
- Verification:
  - Forced-timeout integration test.
- Wave 3 implementation notes:
  - Backend stream now emits `keepalive` heartbeat events during idle periods.
  - Added server-side stream timeout semantics with explicit `run.error` on stalls.
  - Files: `backend/src/app/routes/chat/streaming.py`.

### `[x]` P2-FE-11: Thread-safe optimistic UX

- Owner: Frontend
- Depends on: `P2-FE-01`, `P2-FE-02`, `P2-FE-10`
- Includes:
  - Disable cross-thread send during active stream or isolate by run context.
- Acceptance:
  - Switching threads during streaming does not corrupt message timelines.
- Verification:
  - Stress test with rapid thread switches.
- Wave 3 implementation notes:
  - Thread switching and new-thread creation are locked while a stream is active.
  - Prevents cross-thread optimistic state corruption during in-flight runs.
  - Files: `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/features/workspace/components/SessionsPanel.tsx`.

### `[x]` P2-QA-01: Phase 2 E2E test matrix

- Owner: Full stack
- Depends on: all Phase 2 core tasks
- Scenarios:
  - Multi-thread chat flows.
  - Long streaming runs.
  - Doc open/read.
  - Diff review and approval decisions.
  - Reload/deep-link recovery.
- Acceptance:
  - All critical scenarios pass in documented checklist.
- Wave 3 QA evidence (2026-02-08):
  - Multi-thread flow: created `qa-wave3-a` and `qa-wave3-b`; thread A accumulated chat/docs/runs while thread B remained empty (`GET /api/chat/{thread_id}` snapshots confirmed isolation).
  - Stream lifecycle: `run.started -> agent.status -> message.delta -> message.completed -> run.completed` observed on `POST /api/chat/qa-wave3-a`.
  - Long stream run: `qa-wave3-long` completed with staged edits and `approval.required` without stream errors.
  - Docs open/read: `GET /api/threads/{thread_id}/docs` and `GET /api/threads/{thread_id}/docs/{doc_id}` returned thread-scoped docs with metadata.
  - Review decision matrix:
    - `request_changes` persisted status + review comment.
    - `approve` persisted review and applied doc update/version bump (`the_pitch` version advanced to 2).
    - `reject` persisted review and left target doc unchanged.
  - Reload/deep-link recovery path: `GET /api/chat/{thread_id}` snapshot payload verified for hydration (`thread`, `messages`, `docs`, `runs`, `agent_statuses`, `changesets`).
  - QA-found defect fixed during matrix run: stale `checkpoint_migrations` could mask dropped LangGraph checkpoint tables; fixed via `0003_reset_checkpoint_tables.sql` and startup `ensure_checkpoint_schema()`.

## Workstream E: Additional MVP-Ready Ideas (Recommended)

### `[x]` P2-IDEA-01: Auto-title threads from first user prompt

- Why:
  - Session list becomes meaningful without manual naming.
- Wave 4 implementation notes:
  - Added automatic thread title derivation from the first persisted user message preview.
  - Auto-title is only applied when thread title is still default/empty, so manual titles are preserved.
  - File: `backend/src/app/db/persist_messages_to_db.py`.

### `[x]` P2-IDEA-02: Add "Run log" drawer

- Why:
  - Provides transparent debugging of agent/tool stream events.
- Wave 4 implementation notes:
  - Added a `Run Log` drawer accessible from the workspace header.
  - Drawer shows thread-scoped run lifecycle, agent status transitions, tool call/results, and changeset events in reverse-chronological order.
  - Files: `frontend/app/features/workspace/components/RunLogDrawer.tsx`, `frontend/app/features/workspace/utils/run-log.ts`, `frontend/app/features/workspace/hooks/useWorkspaceChat.ts`, `frontend/app/features/workspace/WorkspaceScreen.tsx`.

### `[x]` P2-IDEA-03: Persist collapsed/expanded panel preferences

- Why:
  - Improves daily usability with minimal complexity.
- Wave 4 implementation notes:
  - Added collapsible left sessions rail and right documents rail controls.
  - Panel preferences persist across reloads via `localStorage` (`idea-maestro-panel-prefs`).
  - Collapsed rails provide lightweight expand controls while preserving core actions.
  - Files: `frontend/app/features/workspace/WorkspaceScreen.tsx`, `frontend/app/features/workspace/components/SessionsPanel.tsx`, `frontend/app/features/workspace/components/DocumentsPanel.tsx`, `frontend/app/features/workspace/constants.ts`.

### `[ ]` P2-IDEA-04: Add review keyboard shortcuts

- Why:
  - Fast approval workflow:
    `A` approve, `R` reject, `C` request changes.

## 7) Execution Order (Refined, Clean-Slate)

### Wave 0: Foundations (contract + schema reset) `[x] Completed 2026-02-08`

1. `P2-BE-00`  
2. `P2-BE-06`  
3. `P2-FE-00`

Wave 0 exit criteria met:
- Canonical schema + migration path active.
- Canonical stream lifecycle contract active.
- Frontend workspace state aligned to canonical entity model.

### Wave 1: Real data baseline (no dummy UI) `[x] Completed 2026-02-08`

1. `P2-BE-01`, `P2-BE-02`, `P2-BE-07`  
2. `P2-FE-01`, `P2-FE-02`, `P2-FE-03`, `P2-FE-04`

Wave 1 exit criteria met:
- Thread list/create/select is API-backed.
- Thread context is URL-driven and survives refresh.
- Documents list/detail are API-backed and thread scoped.

### Wave 2: Review and diff core `[x] Completed 2026-02-08`

1. `P2-BE-03`, `P2-BE-04`, `P2-BE-05`  
2. `P2-FE-06`, `P2-FE-07`, `P2-FE-08`, `P2-FE-09`

Wave 2 exit criteria met:
- Review retrieval APIs return queue + detailed diffs + history.
- Frontend supports queue selection, diff inspection (side-by-side/unified), and full decision matrix with comments.

### Wave 3: Reliability and launch hardening `[x] Completed 2026-02-08`

1. `P2-BE-08`  
2. `P2-FE-05`, `P2-FE-10`, `P2-FE-11`  
3. `P2-QA-01`

Wave 3 exit criteria met:
- Stream heartbeat + timeout semantics are explicit.
- Frontend run/agent lifecycle status visibility is first-class.
- Event dedup/ordering and thread-switch safety guards are active.
- Phase 2 QA matrix executed with pass evidence and production-blocking defects remediated.

### Wave 4: Optional polish

1. `P2-IDEA-01`, `P2-IDEA-02`, `P2-IDEA-03`, `P2-IDEA-04`

## 8) Phase 2 Release Gates

## Gate A: Real Data Ready

- Thread list/create works.
- Docs list/detail works.
- No dummy sessions/docs remain in UI.
- URL-driven thread selection works across reload.

## Gate B: Streaming Trustworthy

- Incremental streaming visible and stable for long responses.
- Agent statuses visible with accurate lifecycle transitions.
- Frontend state is aligned to canonical Phase 2 stream contract.

## Gate C: Review Complete

- User can inspect diffs and submit all decision types.
- Review decisions persist and appear in history.

## Gate D: MVP Signoff

- Phase 2 E2E matrix passes.
- No P0/P1 bugs in core flows:
  threads, chat, docs, review.
- Cold-start migration + deploy checklist is validated on clean DB.

## 9) Explicit Risks and Mitigations

- Risk: event ordering bugs in long streams.
  Mitigation: stable IDs + reducer fixture tests + run-scoped ordering.
- Risk: schema drift between stream producer and client parser.
  Mitigation: typed event contract doc + contract tests.
- Risk: docs history complexity delays rollout.
  Mitigation: launch with minimal immutable `doc_versions` and defer advanced comparison features.
- Risk: thread metadata quality poor at launch.
  Mitigation: auto-title + fallback title + manual rename.

## 10) Definition of Done (Phase 2)

- No static/dummy session/doc content remains in production UI paths.
- Multiple threads are first-class and stable across reload/deep-link.
- Streaming content appears incrementally with agent status clarity.
- Living docs are openable/readable with accurate metadata.
- Diff review UI supports inspect + decision + history.
- QA matrix is documented with pass evidence.
