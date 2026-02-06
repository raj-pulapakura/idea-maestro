from app.agents.prompts.shared_documents import SHARED_DOCUMENTS
from app.agents.prompts.personality_guidance import PERSONALITY_GUIDANCE

def build_sub_agent_prompt(
    sub_agent_name: str,
    short_description: str,
    core_values: str,
    agent_goals: str,
    style_and_tone: str
) -> str:
    return f"""You are {sub_agent_name}, a {short_description}.

# Core Values
{core_values}

# Your Goals as an agent
{agent_goals}

# Style and Tone
{style_and_tone}

The following information is shared by all agents in the system:

# Personality guidance
{PERSONALITY_GUIDANCE}

# Shared Documents
{SHARED_DOCUMENTS}"""
