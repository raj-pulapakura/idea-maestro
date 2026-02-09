# Living Issues Tracker

Last updated: 2026-02-09
Owner: Engineering
Scope: Chat/Agent/Review backend and user-facing workflow reliability

## Purpose
This is a living record of current implementation issues and gaps. The goal is to keep a shared, continuously updated view of technical risk, impact, and planned direction.

## Status Legend
- `open`: not yet addressed
- `in_progress`: currently being implemented
- `blocked`: cannot proceed until a dependency/decision is resolved
- `done`: implemented and verified

## Priority Legend
- `P0`: must address immediately; impacts correctness or core user trust
- `P1`: high impact; should be addressed in the current phase
- `P2`: medium impact; plan after P0/P1
- `P3`: lower urgency polish/optimization

---

## Active Issues

### ISSUE-001: Sub-agent messages are not durably persisted
- Status: `open`
- Priority: `P0`
- Area: Backend persistence / chat history integrity
- Problem:
  - Message persistence wrapper is applied to `maestro` only.
  - Sub-agent conversational outputs are visible during stream but may not survive reload/snapshot reconstruction.
- User/Business Impact:
  - Incomplete thread history after refresh.
  - Reduced trust in system auditability and collaboration continuity.
- References:
  - `backend/src/app/agents/build_workflow.py`
  - `backend/src/app/db/persist_messages_wrapper.py`

### ISSUE-002: Orchestration is single-hop, not a true multi-agent loop
- Status: `open`
- Priority: `P0`
- Area: Backend orchestration model
- Problem:
  - Current top-level flow is effectively `maestro -> selected sub-agent -> END`.
  - No native iterative multi-agent sequence in one run.
- User/Business Impact:
  - Weaker realization of the core product promise (multi-agent refinement loop).
  - More user turns needed to achieve depth of critique/improvement.
- References:
  - `backend/src/app/agents/build_workflow.py`

### ISSUE-003: Maestro routing is brittle (LLM text -> second LLM classifier)
- Status: `open`
- Priority: `P0`
- Area: Backend routing correctness
- Problem:
  - Maestro generates freeform text, then a second model classifies whether to route and to whom.
  - This introduces avoidable ambiguity and failure modes.
- User/Business Impact:
  - Incorrect/no routing when classifier inference is off.
  - Nondeterministic behavior that is difficult to debug.
- References:
  - `backend/src/app/agents/defintions/maestro.py`

### ISSUE-004: Approval semantics mismatch (backend changeset-level vs frontend doc-by-doc affordance)
- Status: `open`
- Priority: `P0`
- Area: Backend/frontend review contract
- Problem:
  - Backend resolves approval at the changeset interrupt level.
  - Frontend presents a per-doc progression pattern (`Approve & Next Doc`) that can imply doc-level commit semantics.
- User/Business Impact:
  - Potential confusion about what is actually approved/applied.
  - Risk of product behavior being interpreted as partial approval support when it is not.
- References:
  - `backend/src/app/agents/nodes/change_set.py`
  - `frontend/app/features/workspace/components/ReviewWorkspace.tsx`

### ISSUE-005: Agent controls in header are mostly non-functional
- Status: `open`
- Priority: `P1`
- Area: Frontend controls / control-plane UX
- Problem:
  - `Pause Agents` exists in UI without backend control path.
- User/Business Impact:
  - Mismatch between visible controls and actual capabilities.
- References:
  - `frontend/app/features/workspace/components/AppHeader.tsx`

### ISSUE-006: Composer hints imply features not implemented (`@`, `#`)
- Status: `open`
- Priority: `P1`
- Area: Prompting UX / routing UX
- Problem:
  - Placeholder indicates mention/tag behavior, but route handling is not implemented in the active contract.
- User/Business Impact:
  - User confusion and expectation mismatch.
- References:
  - `frontend/app/features/workspace/components/ChatComposer.tsx`

### ISSUE-007: Production hardening gaps (security and tenancy)
- Status: `open`
- Priority: `P1`
- Area: Platform hardening
- Problem:
  - Open CORS, no authn/authz, no rate limiting, no tenancy boundaries.
- User/Business Impact:
  - Not safe for external deployment.
- References:
  - `backend/src/app/main.py`

### ISSUE-008: Quality/maintainability cleanup items
- Status: `open`
- Priority: `P2`
- Area: Code quality
- Problem:
  - Naming typo in folder (`defintions`).
- User/Business Impact:
  - Increased maintenance friction and avoidable defects.
- References:
  - `backend/src/app/agents/defintions/`

---

## Next Update Protocol
When closing or updating an issue, append:
- Date
- Owner
- Change summary
- Validation evidence (tests, traces, screenshots, or logs)
