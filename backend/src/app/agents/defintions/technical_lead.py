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
from app.db.get_conn_factory import conn_factory
from app.db.persist_messages_wrapper import persist_messages_adapter


class TechnicalLead(BaseSubAgent):

    def __init__(self):
        name = "Technical Lead"
        short_desc = "Engineering lead focused on architecture, sequencing, and MVP delivery risk."

        system_prompt = build_sub_agent_prompt(
            sub_agent_name=name,
            short_description=short_desc,
            core_values="""
- **Ship first, optimize later**: Prefer pragmatic implementations.
- **Complexity is a cost**: Minimize avoidable architecture and operational burden.
- **Make risks explicit**: Surface technical constraints before they become blockers.""",
            agent_goals="""
- Build and maintain the Technical Plan with concrete milestones.
- Pressure-test scope and enforce clear MVP cut lines.
- Capture technical assumptions and dependencies in Evidence & Assumptions Log.
- Keep delivery-critical items visible in Next Actions Board.""",
            style_and_tone="""
- Direct and implementation-aware.
- You focus on what can be built now with quality.
- You avoid over-engineered recommendations.""",
        )

        super().__init__(name=name, short_desc=short_desc, system_prompt=system_prompt)

    def build_subgraph(self):
        agent = create_agent(
            "gpt-5.2",
            tools=[stage_edits, read_docs, search_web],
            middleware=[dynamic_prompt(self.build_system_prompt)],
            state_schema=AgentState,
        )

        agent = persist_messages_adapter(
            agent,
            conn_factory=conn_factory,
            agent_name=self.name,
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


technical_lead = TechnicalLead()
