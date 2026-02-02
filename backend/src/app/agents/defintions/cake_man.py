from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langgraph.types import Command
from langgraph.config import get_stream_writer
from langchain.tools import ToolRuntime
from app.agents.state import AgentState
from app.agents.BaseSubAgent import BaseSubAgent
from app.agents.prompts.build_sub_agent_prompt import build_sub_agent_prompt
from app.agents.helpers.sub_agent_marker import get_sub_agent_marker
from app.agents.tools.propose_edits import propose_edits


class CakeMan(BaseSubAgent):

    def __init__(self):
        name = "Cake Man"
        short_desc = "A 10x improver and 'wow factor' product designer inside a multi-agent team."

        system_prompt = build_sub_agent_prompt(
          sub_agent_name=name,
          short_description=short_desc,
          core_values="""
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

    def run(self, state: AgentState):
        model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
        ).bind_tools([propose_edits])

        response = model.invoke([
            {"role": "system", "content": self.system_prompt},
            *state["messages"]
        ])

        response_text = response.content + get_sub_agent_marker(self.name)
        state_update = {
            "messages": AIMessage(content=response_text),
            "by_agent": self.name,
        }

        if not response.tool_calls:
            return state_update

        for tool_call in response.tool_calls:
            if tool_call.name != "propose_edits":
                continue

            runtime = ToolRuntime(
                state=state,
                context={},
                config={},
                stream_writer=get_stream_writer(),
                tool_call_id=tool_call.id,
                store=None,
            )

            tool_result = propose_edits.invoke(
                {
                    **(tool_call.args or {}),
                    "runtime": runtime,
                }
            )

            if isinstance(tool_result, Command):
                merged_update = dict(tool_result.update or {})
                merged_update.update(state_update)
                return Command(goto=tool_result.goto, update=merged_update)

        return state_update


cake_man = CakeMan()
