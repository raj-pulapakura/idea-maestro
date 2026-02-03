from app.agents.tools.propose_edits import propose_edits
from app.agents.tools.read_docs import read_docs
from langgraph.prebuilt import ToolNode

tools = [propose_edits, read_docs]
tool_node = ToolNode(tools)