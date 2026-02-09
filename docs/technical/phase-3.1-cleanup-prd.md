# PRD: Phase 3.1 (Cleanup)

Last updated: 2026-02-09
Status: Draft
Owner: Engineering
Scope: Stabilize the core chat/agent/review pipeline before deeper Phase 3 expansion

## 1) Summary
Phase 3.1 focuses on resolving the four highest-risk implementation gaps that currently affect reliability, routing correctness, orchestration depth, and review clarity.

This PRD is intentionally high-level and solution-oriented. Detailed design and API contracts will be defined in a follow-up technical spec.

## 2) Goals
- Preserve complete and trustworthy conversation history across refresh/reload.
- Move from single-hop delegation to a genuine multi-agent orchestration loop.
- Make sub-agent routing behavior more deterministic and debuggable.
- Align review UX semantics with backend approval semantics.

## 3) Non-Goals (for this cleanup wave)
- Full production hardening (authn/authz/rate limiting/tenancy).
- Major visual redesign of frontend workspace.
- Advanced human-in-the-loop policy engine.

## 4) Selected Pressing Issues

### 4.1 ISSUE A: Sub-agent messages are not durably persisted

#### Problem
Current persistence is applied at Maestro-node level, while sub-agent message output is not consistently persisted with the same guarantees.

#### Why this matters
- Thread history can be incomplete after reload.
- Weakens trust, traceability, and incident/debug workflows.

#### Possible high-level solutions
1. **Graph-wide message persistence adapter (recommended direction)**
- Add a standardized persistence layer that runs for any node output containing messages.
- Ensure by-agent attribution is preserved consistently.

2. **Per-subgraph wrapper strategy**
- Wrap each sub-agent node/subgraph with the same persistence wrapper currently used for Maestro.
- Lower conceptual change, but higher risk of drift/duplication.

3. **Streaming-event-to-db fallback recorder**
- Persist from normalized stream events (`message.completed`) if node-level output misses coverage.
- Useful as resilience layer; not preferred as sole source of truth.

---

### 4.2 ISSUE B: Orchestration is single-hop, not true multi-agent loop

#### Problem
The current top-level run usually ends after one routed sub-agent execution, limiting iterative multi-agent collaboration in a single run.

#### Why this matters
- Underdelivers on core product promise of coordinated multi-agent refinement.
- Forces extra user turns for what should be one orchestration cycle.

#### Possible high-level solutions
1. **Supervisor loop with explicit stop conditions (recommended direction)**
- After each sub-agent outcome, route back to Maestro/supervisor.
- Continue until stop criteria are met (e.g., no new edits, confidence threshold, max turns, or approval gate reached).

2. **Plan-then-execute orchestration**
- Maestro first creates a short action plan (ordered agents), then executes sequentially.
- Easier observability, but potentially less adaptive than dynamic looping.

3. **Hybrid loop with guardrails**
- Dynamic routing with hard limits (max N agent turns, max tool calls, budget/time cap).
- Good balance between adaptability and control.

---

### 4.3 ISSUE C: Maestro routing is brittle

#### Problem
Routing currently relies on generating freeform text and then using a second model call to infer intent and target sub-agent.

#### Why this matters
- Compounds uncertainty across two model outputs.
- Harder to reason about route failures and recover quickly.

#### Possible high-level solutions
1. **Single-call structured Maestro output (recommended direction)**
- Maestro returns a strict schema: `{user_message, action, target_agent, rationale}` in one call.
- Remove secondary intent-classifier call.

2. **Rule-assisted routing with schema validation**
- Use deterministic checks for explicit patterns plus schema-driven fallback.
- Improves robustness for common routing intents.

3. **Constrained action vocabulary + retries**
- Restrict allowed actions and normalize agent names with strict validation/retry loop.
- Fails closed to safe text response when validation fails.

---

### 4.4 ISSUE D: Approval semantics mismatch (changeset-level vs doc-level UX cues)

#### Problem
Backend approval is changeset-level, while current review UX can suggest stepwise doc-level approval semantics.

#### Why this matters
- User mental model can diverge from actual commit behavior.
- Increased risk of incorrect expectations in review-heavy workflows.

#### Possible high-level solutions
1. **Make UX explicitly changeset-level (recommended direction for immediate cleanup)**
- Keep backend semantics as-is.
- Update UI copy/actions to make it clear that decision applies to the full changeset.

2. **Introduce true doc-level decisioning in backend**
- Extend approval contract to accept per-doc decisions and partial apply behavior.
- Higher complexity; likely a separate phase.

3. **Two-step model: doc inspection then one final changeset decision**
- Preserve single backend decision point while allowing doc-by-doc browsing.
- Clarify that intermediate doc actions are review progression only, not commit operations.

## 5) Success Criteria (High-Level)
- History consistency: conversation snapshots include all surfaced agent messages for a run.
- Orchestration depth: at least one multi-agent iterative path is supported in a single run.
- Routing reliability: route action is schema-validated and observable as a first-class event.
- Review clarity: no ambiguity in UI about decision scope (changeset vs doc).

## 6) Risks / Open Questions
- How much orchestration autonomy is acceptable before requiring user approval?
- Should approval block all further agent work, or permit non-edit analysis turns?
- What is the canonical source of truth for displayed conversation: persisted messages vs stream event reconstruction?

## 7) Proposed Next Step
Create a design spec for each issue (A-D) with:
- API/state contract deltas
- migration strategy
- instrumentation/test plan
- rollout plan and fallback behavior
