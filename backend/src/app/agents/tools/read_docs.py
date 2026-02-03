"""
a tool to read the docs from the state and return the full content of the docs.
"""

from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from pydantic import BaseModel, Field

from app.agents.state.types import AgentState

class ReadDocsInput(BaseModel):
    doc_ids: list[str] = Field(description="The IDs of the documents to read")

@tool(args_schema=ReadDocsInput)
def read_docs(doc_ids: ReadDocsInput, runtime: ToolRuntime):
    """
    Read the docs from the state and return the full content of the docs.

    Args:
        doc_ids: The IDs of the documents to read.
    """
    state: AgentState = runtime.state
    docs = state.get("docs") or {}
    docs_subset = {doc_id: docs[doc_id] for doc_id in doc_ids}
    return docs_subset