from duckduckgo_search import DDGS
from typing import List, Dict, Any

def search_web(query: str) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo and return a list of results.
    
    Args:
        query (str): The search query
        
    Returns:
        List[Dict[str, Any]]: A list of search results, each containing title and URL
    """
    try:
        results = DDGS().text(query, max_results=10)
        if results:
            return [
                {
                    "title": result["title"],
                    "url": result["href"],
                    "snippet": result.get("body", "")
                }
                for result in results
            ]
        return []
    except Exception as e:
        return [{"error": str(e)}]