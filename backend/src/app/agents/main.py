from langgraph.graph import END, START, StateGraph

from app.agents.defintions.maestro import maestro
from app.agents.state import AgentState

from app.agents.defintions.cake_man import cake_man
from app.db.persist_messages_wrapper import persist_messages_wrapper

from app.db.URL import DB_URL
from app.db.get_conn_factory import conn_factory


def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("maestro", persist_messages_wrapper(maestro, conn_factory=conn_factory))
    workflow.add_edge(START, "maestro")
    workflow.add_edge("maestro", END)

    workflow.add_node(cake_man.name, persist_messages_wrapper(cake_man.run, conn_factory=conn_factory))
    workflow.add_edge("maestro", cake_man.name)
    workflow.add_edge(cake_man.name, END)

    return workflow