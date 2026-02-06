from langgraph.graph import END, START, StateGraph

from app.agents.defintions.maestro import maestro
from app.agents.state.types import AgentState

from app.agents.defintions.cake_man import cake_man
from app.agents.defintions.devils_advocate import devils_advocate
from app.agents.defintions.angel_eyes import angel_eyes
from app.agents.defintions.capital_freak import capital_freak
from app.agents.defintions.buzz import buzz
from app.agents.defintions.mr_t import mr_t
from app.db.persist_messages_wrapper import persist_messages_wrapper

from app.db.get_conn_factory import conn_factory


def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("maestro", persist_messages_wrapper(maestro, conn_factory=conn_factory))
    workflow.add_edge(START, "maestro")
    workflow.add_edge("maestro", END)

    # Add all subagents
    subagents = [
        devils_advocate,
        angel_eyes,
        capital_freak,
        cake_man,
        buzz,
        mr_t
    ]

    for subagent in subagents:
        workflow.add_node(subagent.name, subagent.build_subgraph())

    return workflow
