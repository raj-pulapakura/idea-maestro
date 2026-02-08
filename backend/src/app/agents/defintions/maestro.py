from typing import Optional, TypedDict
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.state.types import AgentState
from app.agents.defintions.cake_man import cake_man
from app.agents.defintions.devils_advocate import devils_advocate
from app.agents.defintions.angel_eyes import angel_eyes
from app.agents.defintions.capital_freak import capital_freak
from app.agents.defintions.buzz import buzz
from app.agents.defintions.mr_t import mr_t


AGENT_NAME = "maestro"

class MaestroAction(TypedDict):
    is_text_response: bool
    is_goto_subagent: bool
    subagent_name: Optional[str]


def _normalize_agent_name(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("_", " ")
    )


def maestro(state: AgentState):
    text_response_model = ChatOpenAI(
        model="gpt-5.2",
    )

    response = text_response_model.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        *state["messages"],
    ])

    action_model = ChatOpenAI(
        model="gpt-5.2",
    ).with_structured_output(MaestroAction, method="json_schema")

    action_response = action_model.invoke([
        {"role": "system", "content": ACTION_DETECTION_PROMPT},
        {"role": "user", "content": f"AI Assistant message: {response.content}"}
    ])

    print("\n\n\n\n")
    print(f"action_response: {action_response}")
    print("\n\n\n\n")

    state_update = {
        "messages": AIMessage(content=response.content),
        "by_agent": AGENT_NAME,
        "next_agent": None,
    }

    if action_response["is_goto_subagent"]:
        selected = action_response.get("subagent_name")
        if isinstance(selected, str):
            normalized_selected = _normalize_agent_name(selected)
            for subagent in subagents:
                if _normalize_agent_name(subagent.name) == normalized_selected:
                    selected = subagent.name
                    break
        state_update["next_agent"] = selected
        return state_update

    return state_update


subagents = [
    devils_advocate,
    angel_eyes,
    capital_freak,
    cake_man,
    buzz,
    mr_t
]

subagents_descriptions = "\n".join([f"- {subagent.name}: {subagent.short_desc}" for subagent in subagents])


SYSTEM_PROMPT = f"""
You are ${AGENT_NAME}, the orchestrator.

You only route user requests to the right sub-agent(s). You do not do the work yourself.

Behavior
- Friendly, casual manager tone.
- Default to delegating whenever possible.
- When delegating, briefly tell the user why.
- You do not ask the user questions about their idea. You are purely a delegator.

Delegation rules
- Do not give detailed instructions.
- Tell the chosen sub-agent they are in charge.
- Refer to sub-agents only by the exact names in Sub-agents descriptions (exact casing). Never invent names.

Multi-agent orchestration rules:
- Only one sub-agent should stage an edit at a time.
- After a sub-agent stages an edit, we must wait for the user to approve or reject the edit.
- This is to prevent multiple sub-agents from staging conflicting edits at the same time.

# Sub-agents descriptions
{subagents_descriptions}"""

ACTION_DETECTION_PROMPT = """
Your simple task is to determine the intended action of the AI assistant.
Given an AI Assistant message such as:
- "Looks like you're app idea could use <reason>. I'm going to hand off to <sub_agent>"
- "What are your thoughts on this?"

You must output a JSON object with the following fields:
- is_text_response: Whether the message is a text response.
- is_goto_subagent: Whether the message is a request to goto a sub-agent.
- subagent_name: The name of the sub-agent to goto if action is "goto_subagent".

Either is_text_response or is_goto_subagent must be true, and the other must be false.
If is_goto_subagent is true, then subagent_name must be the name of a sub-agent exactly as it appears in the AI Assistant message.
"""
