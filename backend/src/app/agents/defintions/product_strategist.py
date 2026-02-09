from langchain.agents import create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langgraph.graph import END, StateGraph

from app.agents.BaseSubAgent import BaseSubAgent
from app.agents.nodes.change_set import (
    apply_changeset_node,
    await_approval_node,
    build_changeset_node,
    reject_changeset_node,
)
from app.agents.prompts.build_docs_summaries_prompt import build_docs_summaries_prompt
from app.agents.prompts.build_sub_agent_prompt import build_sub_agent_prompt
from app.agents.state.types import AgentState
from app.agents.tools.read_docs import read_docs
from app.agents.tools.search_web import search_web
from app.agents.tools.stage_edits import stage_edits


class ProductStrategist(BaseSubAgent):

    def __init__(self):
        name = "Product Strategist"
        short_desc = (
            "Product strategy lead focused on problem clarity, ICP, value proposition, and prioritization."
        )

        system_prompt = build_sub_agent_prompt(
            sub_agent_name=name,
            short_description=short_desc,
            core_values="""
- **Clarity over fluff**: Build crisp problem statements and differentiated positioning.
- **User outcomes over features**: Prioritize user pain and measurable impact.
- **Focus over sprawl**: Keep scope tight enough to ship and learn quickly.""",
            agent_goals="""
- Improve the Product Brief with clearer problem framing, ICP, and value proposition.
- Maintain strong prioritization between core MVP needs and later opportunities.
- Keep the MVP Scope & Non-Goals document explicit and decision-ready.
- Record important tradeoffs in the Risk & Decision Log.""",
            style_and_tone="""
- Practical and structured.
- You write concise, decision-ready edits.
- You avoid generic product jargon and force specificity.""",
        )

        super().__init__(name=name, short_desc=short_desc, system_prompt=system_prompt)

    def build_subgraph(self):
        agent = create_agent(
            "gpt-5.2",
            tools=[stage_edits, read_docs, search_web],
            middleware=[dynamic_prompt(self.build_system_prompt)],
            state_schema=AgentState,
        )

        sg = StateGraph(AgentState)

        sg.add_node("agent", agent)
        sg.add_node("build_changeset", build_changeset_node)
        sg.add_node("await_approval", await_approval_node)
        sg.add_node("apply_changeset", apply_changeset_node)
        sg.add_node("reject_changeset", reject_changeset_node)

        sg.add_edge("agent", "build_changeset")
        sg.add_edge("build_changeset", "await_approval")
        sg.add_edge("apply_changeset", END)
        sg.add_edge("reject_changeset", END)

        sg.set_entry_point("agent")
        return sg.compile()

    def build_system_prompt(self, request: ModelRequest) -> str:
        return f"""{self.system_prompt}

# Current document content summaries
{build_docs_summaries_prompt(request.state)}"""


product_strategist = ProductStrategist()
