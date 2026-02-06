from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langgraph.graph import END, StateGraph
from app.agents.state.types import AgentState
from app.agents.BaseSubAgent import BaseSubAgent
from app.agents.prompts.build_sub_agent_prompt import build_sub_agent_prompt
from app.agents.tools.stage_edits import stage_edits
from app.agents.prompts.build_docs_summaries_prompt import build_docs_summaries_prompt
from app.agents.tools.read_docs import read_docs
from app.agents.tools.search_web import search_web
from langchain.agents import create_agent

from app.agents.nodes.change_set import build_changeset_node, await_approval_node, apply_changeset_node, reject_changeset_node


class Buzz(BaseSubAgent):

    def __init__(self):
        name = "Buzz"
        short_desc = "Marketing and distribution strategist."

        system_prompt = build_sub_agent_prompt(
          sub_agent_name=name,
          short_description=short_desc,
          core_values="""
- **Attention**: Products need to be discovered and talked about.
- **Clarity of message**: Messaging must be crisp, memorable, and differentiated.
- **Realistic channels**: Choose distribution channels that actually work for the target audience.""",
          agent_goals="""
- Define ICP (Ideal Customer Profile) and messaging in **The Pitch** and **GTM Plan**.
- Outline launch strategy and content ideas.
- Choose channels (social, communities, PR, etc.) that fit the product and audience.
- Create shareable moments and growth loops.
- Ensure the product story is compelling and clear.""",
          style_and_tone="""
- Marketing-savvy and channel-aware.
- You think about how products get discovered and shared.
- You're practical about which channels work for which audiences.
- You focus on clarity and differentiation in messaging."""
        )

        super().__init__(
            name=name,
            short_desc=short_desc,
            system_prompt=system_prompt
        )

    def build_subgraph(self):

        agent = create_agent(
                "gpt-5.2",
                tools=[stage_edits, read_docs, search_web],
                middleware=[dynamic_prompt(self.build_system_prompt)],
                state_schema=AgentState
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
        prompt = f"""{self.system_prompt}

# Current document content summaries
{build_docs_summaries_prompt(request.state)}"""

        return prompt


buzz = Buzz()

