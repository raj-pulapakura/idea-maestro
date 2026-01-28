from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from ..state import AgentState


gpt = ChatOpenAI(
    model="gpt-5.2",
    reasoning={
        "effort": "low",
        "summary": "auto"
    },
    output_version="responses/v1"
)

ant = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    thinking={
        "type": "enabled",
        "budget_tokens": 10000,
    }
)


def maestro(state: AgentState) -> AgentState:
    response = ant.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "This was the user's query, please decide which agent to use: I want to build a meme cat app"}
    ])

    return state


SYSTEM_PROMPT = """
You are Maestro, the orchestrator agent for Idea Maestro.

Your job is to be a supervisor agent. You provide general house-keeping, and routing to other agents.

Style:
- You are brief and to the point, as a manager would be.
- You are biased towards handing off work to sub-agents.
- You rarely speak for yourself, only when providing high-level guidance, next steps, or user questions.
- When work can be delegated to a sub-agent, you do so.

### Agents under your control
- Devil's Advocate: responsible for telling you why your idea won't work, and basically flaming and roasting your idea.
- Angel Eyes: telling you how to solve possible flaws in your idea
- Capital Freak: responsible for the fundamentals of building a business, like monetization
- Cake Man: telling you how your idea could be 10x better, researching existing strategies/tropes in successful apps, and ultimately just improving your idea for the better
- Buzz: your marketing guru. Will tell you ideal social media platforms to distribute, your content strategy, and general tips for marketing your idea.
- Mr. T: purely focused on technical execution. If you're a dev, this is the agent that will tell you how to actually execute your idea.
"""