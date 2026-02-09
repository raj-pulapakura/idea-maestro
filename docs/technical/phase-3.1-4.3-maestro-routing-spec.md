# Tech Spec: Phase 3.1 - 4.3 Single-Call Structured Maestro Routing

Last updated: 2026-02-09
Status: Draft
Owner: Engineering
Depends on:
- `/Users/rajpulapakura/Personal Code/idea-maestro/docs/technical/phase-3.1-cleanup-prd.md`
- `/Users/rajpulapakura/Personal Code/idea-maestro/docs/technical/phase-3.1-4.1-message-persistence-spec.md`

## 1) Scope
Replace Maestro’s current two-call routing pattern with a **single structured LLM call** that returns both:
- the user-facing Maestro message
- the routing decision (`delegate` vs `respond`) and target specialist

This spec is limited to routing behavior in the current single-hop orchestration model. Multi-hop looping remains 4.2.

## 2) Problem Statement
Current Maestro flow performs:
1. freeform response generation
2. second LLM call that classifies the generated text into action + target sub-agent

This introduces avoidable ambiguity, extra latency, higher token cost, and harder debugging when the classifier disagrees with the intent of the first call.

Current implementation reference:
- `/Users/rajpulapakura/Personal Code/idea-maestro/backend/src/app/agents/defintions/maestro.py`

## 3) Goals
- Use one model call to produce a validated routing payload.
- Remove the second classifier call entirely.
- Keep user-facing behavior equivalent (friendly routing manager voice).
- Preserve compatibility with 4.1 message persistence semantics.

## 4) Non-Goals
- Introduce supervisor looping (4.2).
- Change specialist prompts/tools.
- Change frontend contracts.

## 5) Requirements

### 5.1 Functional
1. Maestro returns exactly one structured object with message + action.
2. Supported actions for 4.3:
- `delegate`
- `respond`
3. If `delegate`, target agent must be one of current specialists:
- `Product Strategist`
- `Growth Lead`
- `Business Lead`
- `Technical Lead`
4. State update must remain compatible with workflow routing (`next_agent`) and persistence adapter (`messages`, `by_agent`).

### 5.2 Reliability
1. Invalid/partial model payload must fail closed to safe `respond` behavior.
2. Invalid target agent names must not crash routing.
3. Logging must make routing decisions inspectable in backend logs.

### 5.3 Performance
1. Reduce model calls in Maestro from 2 to 1 per turn.
2. Reduce routing latency and token usage relative to current implementation.

## 6) Proposed Design

### 6.1 Structured Output Schema
Define strict schema in Maestro module.

Proposed schema (TypedDict or Pydantic model):
```python
class MaestroDecision(TypedDict):
    user_message: str
    action: Literal["delegate", "respond"]
    target_agent: Optional[str]
    rationale: str
```

Validation rules:
- `user_message` must be non-empty.
- `action == "delegate"` requires non-empty `target_agent`.
- `target_agent` must resolve to one of known specialist names after normalization.

### 6.2 Maestro Node Behavior
Replace current dual-call logic with:
1. `ChatOpenAI(...).with_structured_output(MaestroDecision, method="json_schema").invoke(...)`
2. Validate and normalize decision.
3. Build state update:
- `messages = AIMessage(content=user_message)`
- `by_agent = "maestro"`
- `next_agent = normalized_target_agent if action == "delegate" else None`

Fallback behavior:
- On schema/validation failure, produce deterministic safe response:
  - `user_message`: generic clarification/acknowledgement text
  - `action`: `respond`
  - `next_agent`: `None`

### 6.3 Prompt Contract
Use one system prompt that instructs model to:
- act as orchestrator only
- produce concise user-facing delegation rationale
- choose one action (`delegate` or `respond`)
- when delegating, choose exactly one valid specialist name

No second “action detection” prompt remains.

### 6.4 Integration with 4.1 Persistence
No contract break expected if Maestro keeps output shape:
- `messages` field present with only newly generated AIMessage
- `by_agent = "maestro"`

This is important because 4.1 adapter persists only message deltas and relies on role/agent attribution correctness.

## 7) Files to Update
1. `/Users/rajpulapakura/Personal Code/idea-maestro/backend/src/app/agents/defintions/maestro.py`
- Remove `MaestroAction` and second classifier call.
- Introduce new `MaestroDecision` schema and single-call execution.
- Remove `ACTION_DETECTION_PROMPT`.

2. Optional small helper extraction (if needed):
- `/Users/rajpulapakura/Personal Code/idea-maestro/backend/src/app/agents/helpers/` (normalization/validation utility)

## 8) Migration and Rollout
### 8.1 Migration
- No DB migration required.
- Runtime-only behavior change in Maestro node.

### 8.2 Rollout
1. Implement behind direct code replacement (single path).
2. Run local smoke tests on fresh thread.
3. Verify routing and persistence behavior.

## 9) Validation Plan

### 9.1 Unit Tests (new)
- Valid `delegate` payload maps to expected `next_agent`.
- Valid `respond` payload yields `next_agent = None`.
- Invalid agent name falls back to `respond`.
- Missing/empty fields fall back to safe response.

### 9.2 Integration Tests
- Send chat message -> Maestro delegates to specialist in one pass.
- Persisted Maestro message has `by_agent = "maestro"`.
- No duplicate decision artifacts (classifier call removed).

### 9.3 Regression Checks
- SSE streaming behavior unchanged for message/run events.
- Workflow conditional routing still functions with normalized names.
- Existing frontend timeline renders unchanged.

## 10) Risks and Mitigations
- Risk: Model returns weak/invalid structured output.
  - Mitigation: strict validation + fail-closed fallback.
- Risk: Delegation quality drops with single prompt.
  - Mitigation: explicit routing criteria in system prompt + targeted prompt tuning.
- Risk: Hard-to-debug wrong delegations.
  - Mitigation: log structured `action`, `target_agent`, and normalized target.

## 11) Decisions (Resolved)
1. **`rationale` persistence**: keep internal only in 4.3 (do not persist to DB yet).
2. **`stop_condition_hint` field**: defer to 4.2; do not add preemptively in 4.3 schema.

## 12) Implementation Checklist
- [x] Replace Maestro dual-call flow with single structured call.
- [x] Add strict validation and safe fallback path.
- [x] Remove obsolete classifier prompt/constants.
- [ ] Add unit tests for decision normalization and fallbacks.
- [ ] Run integration smoke test with persistence verification.
