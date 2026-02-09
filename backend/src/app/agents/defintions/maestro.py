from typing import Literal, Optional, TypedDict

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.defintions.business_lead import business_lead
from app.agents.defintions.growth_lead import growth_lead
from app.agents.defintions.product_strategist import product_strategist
from app.agents.defintions.technical_lead import technical_lead
from app.agents.state.types import AgentState


AGENT_NAME = "maestro"


class MaestroDecision(TypedDict):
    user_message: str
    action: Literal["delegate", "respond"]
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


def _fallback_decision() -> MaestroDecision:
    return {
        "user_message": (
            "Thanks for sharing that. I do not have enough confidence to delegate yet, "
            "so I will keep this at the orchestrator layer for now."
        ),
        "action": "respond",
        "target_agent": None,
        "rationale": "fallback_due_to_invalid_or_unavailable_structured_output",
    }


def _normalize_decision(raw: object) -> MaestroDecision:
    if not isinstance(raw, dict):
        return _fallback_decision()

    user_message_raw = raw.get("user_message")
    user_message = user_message_raw.strip() if isinstance(user_message_raw, str) else ""
    if not user_message:
        return _fallback_decision()

    action_raw = raw.get("action")
    action: Literal["delegate", "respond"] = (
        action_raw if action_raw in {"delegate", "respond"} else "respond"
    )

    resolved_target = _resolve_target_agent(raw.get("target_agent"))
    if action == "delegate" and resolved_target is None:
        action = "respond"

    rationale_raw = raw.get("rationale")
    rationale = rationale_raw.strip() if isinstance(rationale_raw, str) else ""

    return {
        "user_message": user_message,
        "action": action,
        "target_agent": resolved_target if action == "delegate" else None,
        "rationale": rationale,
    }


def maestro(state: AgentState):
    decision_model = ChatOpenAI(model="gpt-5.2").with_structured_output(
        MaestroDecision,
        method="json_schema",
    )

    try:
        raw_decision = decision_model.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                *state["messages"],
            ]
        )
        decision = _normalize_decision(raw_decision)
    except Exception:
        decision = _fallback_decision()

    state_update = {
        "messages": AIMessage(content=decision["user_message"]),
        "by_agent": AGENT_NAME,
        "next_agent": None,
    }

    if decision["action"] == "delegate" and decision["target_agent"]:
        state_update["next_agent"] = decision["target_agent"]

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
- Select only one action: delegate or respond.
- If delegating, choose exactly one specialist from the official roster.
- Refer to specialists only by exact roster names (exact casing).
- Do not invent specialist names.

Output contract
- Return structured output with fields:
  - user_message: concise user-facing text
  - action: "delegate" or "respond"
  - target_agent: specialist name when action is "delegate", otherwise null
  - rationale: short internal reason for the action

Multi-agent orchestration constraints
- Only one specialist should stage an edit at a time.
- After a specialist stages edits, user approval is required before more staged edits.

# Specialist roster
{subagents_descriptions}
"""
