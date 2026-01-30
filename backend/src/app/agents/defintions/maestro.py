from typing import Literal, Optional, TypedDict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langgraph.types import Command

from app.agents.state import AgentState
from app.agents.defintions.cake_man import cake_man


AGENT_NAME = "maestro"

class MaestroAction(TypedDict):
    is_text_response: bool
    is_goto_subagent: bool
    subagent_name: Optional[str]


def maestro(state: AgentState):
    text_response_model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
    )

    response = text_response_model.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        *state["messages"],
    ])

    action_model = ChatAnthropic(
        model="claude-haiku-4-5-20251001" # small model as this is a simple task
    ).with_structured_output(MaestroAction, method="json_schema")

    action_response = action_model.invoke([
        {"role": "system", "content": ACTION_DETECTION_PROMPT},
        {"role": "user", "content": f"AI Assistant message: {response.content}"}
    ])

    state_update = {
        "messages": AIMessage(content=response.content),
        "by_agent": AGENT_NAME
    }

    if action_response["is_goto_subagent"]:
        return Command(goto=action_response["subagent_name"], update=state_update)

    return state_update


subagents = [
    cake_man
]

subagents_descriptions = "\n".join([f"- {subagent.name}: {subagent.short_desc}" for subagent in subagents])


SYSTEM_PROMPT = f"""
You are ${AGENT_NAME}, the orchestrator agent.

Your job is to be a supervisor agent. You provide general house-keeping, and routing to other agents.

# Style:
- You are like a very friendly and casual manager.
- You are biased towards handing off work to sub-agents.
- When work can be delegated to a sub-agent, you do so.
- However, you do speak for yourself when providing high-level guidance, or just housekeeping, such as:
    - telling the user what's happening in the system
    - telling the user which sub-agent you are handing off to
- If you hand off work to a sub-agent, you like to give the user a reason why you're doing so.
- When you refer to a sub-agens, you always use the name given in the "Sub-agents descriptions" section (with exact casing). Do not make up names.

# Sub-agents descriptions
{subagents_descriptions}

# Outputs (text response)
You generally go for (these are just examples, feel free to vary the wording) (and also these are not limitations):
- "Looks like you're app idea could use <reason>. I'm going to hand off to <sub_agent>"
"""

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