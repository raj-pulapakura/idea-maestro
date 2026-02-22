from langgraph.graph import END, START, StateGraph

from app.agents.defintions.maestro import maestro
from app.agents.state.types import AgentState

from app.agents.defintions.product_strategist import product_strategist
from app.agents.defintions.growth_lead import growth_lead
from app.agents.defintions.business_lead import business_lead
from app.agents.defintions.technical_lead import technical_lead
from app.db.persist_messages_wrapper import persist_messages_adapter

from app.db.get_conn_factory import conn_factory


def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node(
        "maestro",
        persist_messages_adapter(maestro, conn_factory=conn_factory, agent_name="maestro"),
    )
    workflow.add_edge(START, "maestro")

    # Add all subagents
    subagents = [
        product_strategist,
        growth_lead,
        business_lead,
        technical_lead,
    ]

    for subagent in subagents:
        workflow.add_node(subagent.name, subagent.build_subgraph())
        workflow.add_edge(subagent.name, "maestro")

    route_map = {
        subagent.name: subagent.name for subagent in subagents
    }
    route_map["__end__"] = END

    normalized_route_map = {
        name.strip()
        .lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("_", " "): name
        for name in route_map
        if name != "__end__"
    }

    def route_from_maestro(state: AgentState) -> str:
        target = state.get("next_agent")
        if isinstance(target, str):
            if target in route_map:
                return target
            normalized_target = (
                target.strip()
                .lower()
                .replace("’", "'")
                .replace("‘", "'")
                .replace("`", "'")
                .replace("_", " ")
            )
            mapped = normalized_route_map.get(normalized_target)
            if mapped:
                return mapped
        return "__end__"

    workflow.add_conditional_edges("maestro", route_from_maestro, route_map)

    return workflow
