import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def search_web(query: str) -> List[Dict[str, Any]]:
    """Search the web using DuckDuckGo."""
    try:
        logger.info(f"Searching web for: {query}")
        
        with DDGS() as ddgs:
            # Get raw results and convert to list immediately
            raw_results = list(ddgs.text(query, max_results=10))
            logger.info(f"Received {len(raw_results)} raw results")
            
            if raw_results:
                formatted_results = []
                for result in raw_results:
                    # Try multiple possible URL fields
                    url = result.get('link') or result.get('url')
                    title = result.get('title', '')
                    
                    if url:
                        formatted_results.append({
                            "title": title,
                            "url": url
                        })
                
                return formatted_results
            else:
                logger.warning("No search results found")
                return []
                
    except Exception as e:
        logger.error(f"Error in search_web: {str(e)}")
        raise