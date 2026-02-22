from typing import Literal, Optional, TypedDict

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.defintions.business_lead import business_lead
from app.agents.defintions.growth_lead import growth_lead
from app.agents.defintions.product_strategist import product_strategist
from app.agents.defintions.technical_lead import technical_lead
from app.agents.state.types import AgentState


AGENT_NAME = "maestro"
MAX_CONSECUTIVE_NOOP = 2


class MaestroDecision(TypedDict):
    user_message: str
    action: Literal["delegate", "respond", "stop"]
    target_agent: Optional[str]
    rationale: str


def _normalize_agent_name(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("_", " ")
    )


def _resolve_target_agent(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None

    normalized_value = _normalize_agent_name(value)
    return normalized_subagent_map.get(normalized_value)


def _fallback_decision(reason: str) -> MaestroDecision:
    return {
        "user_message": (
            "Thanks for sharing that. I do not have enough confidence to delegate yet, "
            "so I will stop this run here for now."
        ),
        "action": "stop",
        "target_agent": None,
        "rationale": reason,
    }


def _normalize_decision(raw: object) -> tuple[MaestroDecision, str | None]:
    if not isinstance(raw, dict):
        return _fallback_decision("invalid_decision_payload"), "invalid_decision_payload"

    user_message_raw = raw.get("user_message")
    user_message = user_message_raw.strip() if isinstance(user_message_raw, str) else ""
    if not user_message:
        return _fallback_decision("empty_user_message"), "empty_user_message"

    action_raw = raw.get("action")
    action: Literal["delegate", "respond", "stop"] = (
        action_raw if action_raw in {"delegate", "respond", "stop"} else "respond"
    )

    resolved_target = _resolve_target_agent(raw.get("target_agent"))
    error: str | None = None
    if action == "delegate" and resolved_target is None:
        action = "respond"
        error = "invalid_target_agent"

    rationale_raw = raw.get("rationale")
    rationale = rationale_raw.strip() if isinstance(rationale_raw, str) else ""

    return (
        {
            "user_message": user_message,
            "action": action,
            "target_agent": resolved_target if action == "delegate" else None,
            "rationale": rationale,
        },
        error,
    )


def _calculate_consecutive_noop_count(state: AgentState) -> int:
    previous_action = state.get("last_supervisor_action")
    prior_noop_count = int(state.get("consecutive_noop_count") or 0)

    if previous_action != "delegate":
        return prior_noop_count

    history = state.get("history") or []
    cursor = int(state.get("history_cursor_at_last_delegate") or 0)
    had_activity = len(history) > cursor
    if had_activity:
        return 0

    return prior_noop_count + 1


def _guardrail_stop_update(
    *,
    message: str,
    iteration_count: int,
    max_iterations: int,
    consecutive_noop_count: int,
    error: str | None,
) -> dict:
    return {
        "messages": AIMessage(content=message),
        "by_agent": AGENT_NAME,
        "next_agent": None,
        "iteration_count": iteration_count,
        "max_iterations": max_iterations,
        "loop_status": "guardrail_stop",
        "last_routing_error": error,
        "consecutive_noop_count": consecutive_noop_count,
        "last_supervisor_action": "stop",
    }


def maestro(state: AgentState):
    iteration_count = int(state.get("iteration_count") or 0)
    max_iterations = int(state.get("max_iterations") or 4)
    consecutive_noop_count = _calculate_consecutive_noop_count(state)

    if iteration_count >= max_iterations:
        return _guardrail_stop_update(
            message=(
                "I am stopping here because we reached the loop limit for this run. "
                "Please review the current outputs and continue with a new message if needed."
            ),
            iteration_count=iteration_count,
            max_iterations=max_iterations,
            consecutive_noop_count=consecutive_noop_count,
            error="max_iterations_reached",
        )

    if consecutive_noop_count >= MAX_CONSECUTIVE_NOOP:
        return _guardrail_stop_update(
            message=(
                "I am stopping here because recent delegated turns did not produce actionable progress. "
                "Please provide additional direction to continue."
            ),
            iteration_count=iteration_count,
            max_iterations=max_iterations,
            consecutive_noop_count=consecutive_noop_count,
            error="consecutive_noop_guardrail",
        )

    decision_model = ChatOpenAI(model="gpt-5.2").with_structured_output(
        MaestroDecision,
        method="json_schema",
    )

    validation_error: str | None = None
    try:
        raw_decision = decision_model.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                *state["messages"],
            ]
        )
        decision, validation_error = _normalize_decision(raw_decision)
    except Exception:
        validation_error = "structured_output_exception"
        decision = _fallback_decision(validation_error)

    state_update = {
        "messages": AIMessage(content=decision["user_message"]),
        "by_agent": AGENT_NAME,
        "next_agent": None,
        "iteration_count": iteration_count,
        "max_iterations": max_iterations,
        "loop_status": "running",
        "last_routing_error": validation_error,
        "consecutive_noop_count": consecutive_noop_count,
        "last_supervisor_action": decision["action"],
    }

    if decision["action"] == "delegate" and decision["target_agent"]:
        state_update["next_agent"] = decision["target_agent"]
        state_update["iteration_count"] = iteration_count + 1
        state_update["history_cursor_at_last_delegate"] = len(state.get("history") or [])
    else:
        state_update["loop_status"] = "stopped"

    return state_update


subagents = [
    product_strategist,
    growth_lead,
    business_lead,
    technical_lead,
]

normalized_subagent_map = {
    _normalize_agent_name(subagent.name): subagent.name for subagent in subagents
}

subagents_descriptions = "\n".join(
    [f"- {subagent.name}: {subagent.short_desc}" for subagent in subagents]
)


SYSTEM_PROMPT = f"""
You are ${AGENT_NAME}, the orchestrator.

You only route user requests to the right sub-agent(s). You do not do specialist work yourself.

Behavior
- Friendly, casual manager tone.
- Default to delegating whenever possible.
- When delegating, briefly tell the user why.
- If delegation is not appropriate, provide a concise direct response.

Delegation rules
- Select one action: delegate, respond, or stop.
- If delegating, choose exactly one specialist from the official roster.
- Refer to specialists only by exact roster names (exact casing).
- Do not invent specialist names.

Output contract
- Return structured output with fields:
  - user_message: concise user-facing text
  - action: "delegate", "respond", or "stop"
  - target_agent: specialist name when action is "delegate", otherwise null
  - rationale: short internal reason for the action

Multi-agent orchestration constraints
- Only one specialist should stage an edit at a time.
- After a specialist stages edits, user approval is required before more staged edits.

# Specialist roster
{subagents_descriptions}
"""
