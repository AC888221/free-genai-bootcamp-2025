import logging
from typing import List, Dict, Any, Tuple
from duckduckgo_search import DDGS
import json
import re
import asyncio
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track last request time globally
last_request_time = 0
MIN_REQUEST_INTERVAL = 30  # Minimum seconds between requests

class SearchError:
    RATE_LIMIT = "rate_limit"
    NETWORK = "network_error"
    NO_RESULTS = "no_results"

async def search_web(query: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search the web using DuckDuckGo.
    Returns: Tuple of (results, status)
    - results: List of search results
    - status: Dictionary containing status information
    """
    try:
        logger.info(f"Searching web for: {query}")
        
        # Check if we need to wait due to rate limiting
        current_time = time()
        time_since_last = current_time - last_request_time
        if time_since_last < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - time_since_last
            return [], {
                "error": SearchError.RATE_LIMIT,
                "message": f"Please wait {wait_time:.0f} seconds before trying again to avoid rate limits.",
                "wait_time": wait_time
            }
        
        # Make a single query to one site
        search_query = f"{query} site:mojim.com"
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=5))
                global last_request_time
                last_request_time = time()
                
                formatted_results = []
                seen_urls = set()
                
                for result in results:
                    # Try different possible keys for URL
                    url = None
                    for key in ['link', 'url', 'href']:
                        if key in result and result[key]:
                            url = result[key]
                            break
                    
                    title = result.get('title', '')
                    
                    if url and url not in seen_urls:
                        logger.info(f"Found result: {title} at {url}")
                        formatted_results.append({
                            "title": title,
                            "url": url
                        })
                        seen_urls.add(url)
                
                if not formatted_results:
                    return [], {
                        "error": SearchError.NO_RESULTS,
                        "message": "No lyrics found. Please try a different search term or wait a moment before trying again."
                    }
                
                logger.info(f"Found {len(formatted_results)} unique URLs")
                return formatted_results[:5], {
                    "success": True,
                    "message": f"Found {len(formatted_results)} results"
                }
                
        except Exception as e:
            if "ratelimit" in str(e).lower():
                return [], {
                    "error": SearchError.RATE_LIMIT,
                    "message": "Search rate limit reached. Please wait 30 seconds before trying again.",
                    "wait_time": MIN_REQUEST_INTERVAL
                }
            else:
                logger.error(f"Search error: {str(e)}")
                return [], {
                    "error": SearchError.NETWORK,
                    "message": f"Error performing search: {str(e)}"
                }
                
    except Exception as e:
        logger.error(f"Error in search_web: {str(e)}")
        return [], {
            "error": SearchError.NETWORK,
            "message": f"Unexpected error: {str(e)}"
        }

def is_lyrics_site(url: str) -> bool:
    """Check if the URL is likely a lyrics website."""
    lyrics_domains = [
        'lyrics', 'lyric', 'musixmatch', 'genius', 'azlyrics',
        '歌词', 'songlyrics', 'metrolyrics', '歌詞'
    ]
    return any(domain in url.lower() for domain in lyrics_domains)