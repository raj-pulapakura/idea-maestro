from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agents.helpers.emit_event import emit_event
from app.agents.state.types import AgentState


class ProposedEdit(BaseModel):
    doc_id: str = Field(description="The ID of the document to edit")
    new_content: str = Field(description="The new content of the document. Provide the full content, not just a diff.")


class ProposedEditsInput(BaseModel):
    edits: list[ProposedEdit] = Field(description="A list of proposed edits to the documents")
    summary: str = Field(description="Short summary of the proposed edits")
    by: str = Field(description="Name of the agent proposing the edits")


@tool(args_schema=ProposedEditsInput)
def propose_edits(edits: list[ProposedEdit], summary: str, by: str, runtime: ToolRuntime):
    """
    Propose edits to one or more documents. Does not mutate docs.

    Args:
        edits: A list of proposed edits to the documents.
        summary: Short summary of the proposed edits
        by: Name of the agent proposing the edits
    """
    state: AgentState = runtime.state
    docs = state.get("docs") or {}
    normalized_edits = [edit.model_dump() for edit in edits]

    for edit in normalized_edits:
        doc_id = edit["doc_id"]
        if doc_id not in docs:
            raise ValueError(f"Unknown doc_id: {doc_id}")

    emit_event(
        "agent.proposed_edits",
        {
            "by": by,
            "docs": [e["doc_id"] for e in normalized_edits],
            "summary": summary,
        },
    )

    return Command(
        update={
            "proposed_edits": normalized_edits,
            "proposal_summary": summary,
            "proposal_by": by,
            "messages": [
                ToolMessage("Successfully proposed edits", tool_call_id=runtime.tool_call_id)
            ]
        },
        goto="build_changeset",
    )
