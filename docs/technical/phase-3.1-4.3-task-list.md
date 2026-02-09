# Phase 3.1 - 4.3 Task List (Single-Call Maestro Routing)

Last updated: 2026-02-10
Owner: Engineering
Status: In progress
Spec: `/Users/rajpulapakura/Personal Code/idea-maestro/docs/technical/phase-3.1-4.3-maestro-routing-spec.md`

## Execution Tasks

1. Maestro routing refactor
- [x] Replace dual-call flow with one structured output call.
- [x] Remove classifier prompt and `MaestroAction` model.
- [x] Add strict normalization/validation for `action` and `target_agent`.
- [x] Add safe fail-closed fallback (`respond`, no delegation).

2. Contract compatibility
- [x] Preserve state output shape expected by workflow and 4.1 persistence (`messages`, `by_agent`, `next_agent`).
- [x] Ensure delegated target matches canonical specialist names.

3. Validation
- [x] Compile-check modified backend modules.
- [ ] Smoke-check imports for workflow path in runtime environment.
- [x] Document any local validation limits.

4. Documentation updates
- [x] Mark this task list with implementation outcome.
- [x] Update checklist progress in 4.3 spec.

## Outcome Note
- Core 4.3 refactor is implemented in `maestro.py`: single structured call, strict normalization, safe fallback.
- Local runtime import smoke-check is blocked in this shell by Python package mismatch (`ImportError` for `create_agent` from `langchain.agents`), so end-to-end runtime validation should be run in the project runtime container/venv.
