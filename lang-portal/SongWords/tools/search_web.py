import logging
from typing import List, Dict, Any, Tuple
from duckduckgo_search import DDGS
import json
import re
import asyncio
from time import time
from functools import lru_cache
import hashlib
from .blocked_sites import BlockedSitesTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track last request time globally
last_request_time = 0
MIN_REQUEST_INTERVAL = 30  # Minimum seconds between requests
CACHE_DURATION = 3600  # Cache results for 1 hour

# Initialize blocked sites tracker
blocked_sites = BlockedSitesTracker()

class SearchError:
    RATE_LIMIT = "rate_limit"
    NETWORK = "network_error"
    NO_RESULTS = "no_results"

# Cache for search results
search_cache = {}

def _generate_cache_key(query: str) -> str:
    """Generate a unique cache key for a search query."""
    return hashlib.md5(query.encode()).hexdigest()

def _is_cache_valid(timestamp: float) -> bool:
    """Check if cached result is still valid."""
    return (time() - timestamp) < CACHE_DURATION

async def search_web(query: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Search the web using DuckDuckGo with blocked sites exclusion."""
    global last_request_time
    
    try:
        logger.info(f"Starting web search for: {query}")
        
        # Generate exclusion string for blocked sites
        exclusions = []
        for domain in blocked_sites.get_blocked_domains_for_search():
            exclusions.append(f"-site:{domain}")
        
        # Remove mojim.com if it's in the blocked domains
        search_query = query
        if "mojim.com" not in blocked_sites.get_blocked_domains_for_search():
            search_query += " site:mojim.com"
        search_query += f" {' '.join(exclusions)}"
        logger.info(f"Modified search query: {search_query}")
        
        # Check rate limiting
        current_time = time()
        time_since_last = current_time - last_request_time
        if time_since_last < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - time_since_last
            return [], {
                "error": SearchError.RATE_LIMIT,
                "message": f"Please wait {wait_time:.0f} seconds before trying again to avoid rate limits.",
                "wait_time": wait_time
            }
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=5))
                last_request_time = time()
                
                formatted_results = []
                seen_urls = set()
                
                for result in results:
                    url = None
                    for key in ['link', 'url', 'href']:
                        if key in result and result[key]:
                            url = result[key]
                            break
                    
                    title = result.get('title', '')
                    
                    # Double check the URL isn't from a blocked site
                    if url and url not in seen_urls and not blocked_sites.is_site_blocked(url):
                        logger.info(f"Found result: {title} at {url}")
                        formatted_results.append({
                            "title": title,
                            "url": url
                        })
                        seen_urls.add(url)
                
                if not formatted_results:
                    logger.warning("No non-blocked results found")
                    return [], {
                        "error": SearchError.NO_RESULTS,
                        "message": "No accessible lyrics found. All known sources are temporarily blocked."
                    }
                
                logger.info(f"Found {len(formatted_results)} unique, non-blocked URLs")
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