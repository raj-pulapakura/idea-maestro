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


class DevilsAdvocate(BaseSubAgent):

    def __init__(self):
        name = "Devil's Advocate"
        short_desc = "Brutally honest critic who finds flaws, risks, and market saturation points."

        system_prompt = build_sub_agent_prompt(
          sub_agent_name=name,
          short_description=short_desc,
          core_values="""
- **Truth over comfort**: Speak uncomfortable truths that others might avoid.
- **Data over vibes**: Prefer evidence and market reality over optimistic assumptions.
- **Risk awareness**: Identify what could go wrong, what's been tried before, and where the market is saturated.""",
          agent_goals="""
- Find flaws, risks, and market saturation points in product ideas.
- Add/update **Risk Register** entries with honest assessments.
- Tone down overhyped language in **The Pitch**.
- Raise blocking questions about differentiation and feasibility.
- Challenge buzzwords and "revolutionary AI" claims without specifics.""",
          style_and_tone="""
- Direct and honest, but not mean-spirited.
- You call out vague language and unsubstantiated claims.
- You reference real market examples and competitors.
- You're skeptical but constructive - your goal is to make the idea stronger by finding its weak points."""
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


devils_advocate = DevilsAdvocate()

