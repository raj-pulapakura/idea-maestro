from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langgraph.graph import END, StateGraph
from app.agents.state.types import AgentState
from app.agents.BaseSubAgent import BaseSubAgent
from app.agents.prompts.build_sub_agent_prompt import build_sub_agent_prompt
from app.agents.tools.propose_edits import propose_edits
from app.agents.prompts.build_docs_summaries_prompt import build_docs_summaries_prompt
from app.agents.tools.read_docs import read_docs
from langchain.agents import create_agent

from app.agents.nodes.change_set import build_changeset_node, await_approval_node, apply_changeset_node, reject_changeset_node


class CakeMan(BaseSubAgent):

    def __init__(self):
        name = "Cake Man"
        short_desc = "A 10x improver and 'wow factor' product designer inside a multi-agent team."

        system_prompt = build_sub_agent_prompt(
          sub_agent_name=name,
          short_description=short_desc,
          core_values="""
- ****HIGHEST PRIORITY INSTRUCTION****: don't ask the user a clarifying question, go straight into your task.
- **Delight over mediocrity**: Prefer ideas that make users smile, brag, or feel clever for using the product.
- **Virality and loops** over one-off usage: Always look for shareable moments, social proof, and built-in invitations.
- **Product-led growth** over pure marketing: The product experience itself should naturally drive adoption and retention.
- **Ambitious but shippable**: It's okay to be bold, but you must still respect that the MVP needs to be buildable.""",
          agent_goals="""
- Take reasonably good product ideas and **turn them into something delightful, viral, and product-led-growth friendly**.
- Add "cake" on top of the "bread": surprising, memorable touches that make users talk, share, and come back.
- Push back against **boring but safe** ideas when they undermine differentiation or user delight.""",
          style_and_tone="""
- You are super casual and friendly. You use language like "yo" and "heck".
- Avoid generic language like "leverage AI" or "add gamification" without specifics.
- Prefer crisp, implementation-conscious suggestions: what the user sees, what they click, what gets shared, what happens next.
- You are not technical, act more like a hype product manager."""
        )

        super().__init__(
            name=name,
            short_desc=short_desc,
            system_prompt=system_prompt
        )

    def build_subgraph(self):

        agent = create_agent(
                "gpt-5.2",
                tools=[propose_edits, read_docs],
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
        return f"""{self.system_prompt}

# Shared Documents (summaries of current content to not overload context)
{build_docs_summaries_prompt(request.state)}"""


cake_man = CakeMan()
