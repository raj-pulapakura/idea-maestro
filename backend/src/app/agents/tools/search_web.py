"""
A tool to search the web for information.
"""

from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from pydantic import BaseModel, Field

from ddgs import DDGS


class SearchWebInput(BaseModel):
    query: str = Field(description="The search query to look up on the web")
    max_results: int = Field(default=5, description="Maximum number of search results to return (default: 5)")


@tool(args_schema=SearchWebInput)
def search_web(query: str, max_results: int = 5):
    """
    Search the web for information using DuckDuckGo search engine.
    Use this tool when you need to find current information, market data, competitor analysis,
    case studies, or any information that requires web search.

    Args:
        query: The search query to look up on the web.
        max_results: Maximum number of search results to return (default: 5).
    """
    if DDGS is None:
        return "Error: duckduckgo-search library is not installed. Please install it with: pip install duckduckgo-search"
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"No results found for query: {query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                href = result.get("href", "")
                formatted_results.append(f"{i}. {title}\n   {body}\n   Source: {href}\n")
            
            return "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching the web: {str(e)}"

