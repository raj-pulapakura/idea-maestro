from langgraph.graph import END, START, StateGraph

from app.agents.defintions.maestro import maestro
from app.agents.state import AgentState

from app.agents.defintions.cake_man import cake_man
from app.db.persist_messages_wrapper import persist_messages_wrapper

from app.db.URL import DB_URL
from app.db.get_conn_factory import conn_factory
from app.agents.nodes.change_set import (
    build_changeset_node,
    await_approval_node,
    apply_changeset_node,
    reject_changeset_node,
)


def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("maestro", persist_messages_wrapper(maestro, conn_factory=conn_factory))
    workflow.add_edge(START, "maestro")
    workflow.add_edge("maestro", END)

    workflow.add_node(cake_man.name, persist_messages_wrapper(cake_man.run, conn_factory=conn_factory))
    workflow.add_edge("maestro", cake_man.name)
    workflow.add_edge(cake_man.name, END)

    workflow.add_node("build_changeset", build_changeset_node)
    workflow.add_node("await_approval", await_approval_node)
    workflow.add_node("apply_changeset", apply_changeset_node)
    workflow.add_node("reject_changeset", reject_changeset_node)

    workflow.add_edge("build_changeset", "await_approval")
    workflow.add_edge("apply_changeset", "maestro")
    workflow.add_edge("reject_changeset", "maestro")

    return workflow
