"""Web search tools for the agent."""

from langchain.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for information about a topic.
    
    Args:
        query: The search query string
        
    Returns:
        Search results formatted as text
    """
    from duckduckgo_search import DDGS
    
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No search results found."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('href', '')
            formatted_results.append(f"{i}. {title}\n{body}\n{url}")
        
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Search failed: {str(e)}"