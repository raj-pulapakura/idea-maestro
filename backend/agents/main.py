from langgraph.graph import END, START, StateGraph

from .defintions.maestro import maestro
from .state import AgentState





def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)


    workflow.add_node("maestro", maestro)
    # workflow.add_node("devil_advocate", devils_advocate)
    # workflow.add_node("angel_eyes", angel_eyes)
    # workflow.add_node("capital_freak", capital_freak)
    # workflow.add_node("cake_man", cake_man)
    # workflow.add_node("buzz", buzz)
    # workflow.add_node("mr_t", mr_t)
    #     workflow.add_edge("suggest_edit", "approve_edit")
    # workflow.add_edge("approve_edit", "make_edit")
    # workflow.add_edge("make_edit", END)
    # workflow.add_edge("cancel", END)

    workflow.add_edge(START, "maestro")
    workflow.add_edge("maestro", END)

    return workflow