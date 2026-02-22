from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agents.helpers.emit_event import emit_event
from app.agents.state.types import AgentState


class StagedEdit(BaseModel):
    doc_id: str = Field(description="The ID of the document to edit")
    new_content: str = Field(description="The new content of the document. Provide the full content, not just a diff.")


class StagedEditsInput(BaseModel):
    edits: list[StagedEdit] = Field(description="A list of staged edits to the documents")
    summary: str = Field(description="Short summary of the staged edits")
    by: str = Field(description="Name of the agent staging the edits")


@tool(args_schema=StagedEditsInput)
def stage_edits(edits: list[StagedEdit], summary: str, by: str, runtime: ToolRuntime):
    """
    After seeking inputs from the user, use this tool to commit the edits to the documents from which the user can approve them.

    Args:
        edits: A list of staged edits to the documents.
        summary: Short summary of the staged edits
        by: Name of the agent staging the edits
    """
    state: AgentState = runtime.state
    docs = state.get("docs") or {}
    normalized_edits = [edit.model_dump() for edit in edits]

    for edit in normalized_edits:
        doc_id = edit["doc_id"]
        if doc_id not in docs:
            raise ValueError(f"Unknown doc_id: {doc_id}")

    emit_event(
        "agent.staged_edits",
        {
            "by": by,
            "docs": [e["doc_id"] for e in normalized_edits],
            "summary": summary,
        },
    )

    return Command(
        update={
            "staged_edits": normalized_edits,
            "staged_edits_summary": summary,
            "staged_edits_by": by,
            "history": [
                {
                    "type": "specialist_activity",
                    "activity": "edits_staged",
                    "by": by,
                    "docs": [e["doc_id"] for e in normalized_edits],
                }
            ],
            "messages": [
                ToolMessage("Successfully staged edits", tool_call_id=runtime.tool_call_id)
            ]
        },
        goto="build_changeset",
    )
