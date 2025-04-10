import logging
from typing import List, Dict, Any, Tuple, Optional
from duckduckgo_search import DDGS
import json
import re
import asyncio
from time import time
from functools import lru_cache
import hashlib
from .excluded_sites import ExcludedSitesTracker
from hanziconv import HanziConv
from .text_processing import process_chinese_text
import random
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track last request time globally
last_request_time = 0
MIN_REQUEST_INTERVAL = 30  # Minimum seconds between requests
CACHE_DURATION = 3600  # Cache results for 1 hour

# Initialize excluded sites tracker
excluded_sites = ExcludedSitesTracker()

class SearchError:
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    NO_RESULTS = "no_results"
    ACCESS_DENIED = "access_denied"
    FETCH_ERROR = "fetch_error"
    INVALID_QUERY = "invalid_query"

# Cache for search results
search_cache = {}

def _generate_cache_key(query: str) -> str:
    """Generate a unique cache key for a search query."""
    return hashlib.md5(query.encode()).hexdigest()

def _is_cache_valid(timestamp: float) -> bool:
    """Check if cached result is still valid."""
    return (time() - timestamp) < CACHE_DURATION

async def get_page_content(url: str) -> str:
    """Fetch the content of a web page."""
    try:
        # Random delay between requests
        delay = random.uniform(1, 3)
        await asyncio.sleep(delay)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    logger.warning(f"Access denied or server error. Status: {response.status}")
                    return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return ""

def handle_exclusion(url: str, error_info: Dict[str, Any], tracker: ExcludedSitesTracker = None) -> bool:
    """Handle adding sites to the exclusion list based on specific errors.
    Returns True if site was excluded, False otherwise."""
    if error_info.get("error") in [SearchError.FETCH_ERROR, SearchError.NETWORK_ERROR]:
        try:
            domain = url.split('/')[2]
            logger.warning(f"Adding {domain} to excluded sites due to error.")
            if tracker is not None:
                tracker.add_excluded_site(domain)
                return True
        except Exception as e:
            logger.error(f"Error adding domain to exclusion list: {str(e)}")
    return False

async def search_web(query: str, excluded_sites: ExcludedSitesTracker = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Search the web using DuckDuckGo with excluded sites filtering."""
    global last_request_time
    
    # Input validation
    if not query:
        return [], {"error": SearchError.INVALID_QUERY, "message": "Query cannot be empty"}
    if len(query) > 500:  # Reasonable limit for query length
        return [], {"error": SearchError.INVALID_QUERY, "message": "Query too long"}
    
    # Rate limiting check
    if _check_rate_limit():
        return _get_rate_limit_response()
    
    try:
        logger.info(f"Starting web search for: {query}")
        
        # Process the query text
        simplified_query, was_converted = process_chinese_text(query)
        if was_converted:
            logger.info(f"Converted query from Traditional to Simplified Chinese: {query} -> {simplified_query}")
            query = simplified_query
        
        # Generate exclusion string for excluded sites
        exclusions = []
        if excluded_sites is not None:
            for domain in excluded_sites.get_excluded_domains_for_search():
                exclusions.append(f"-site:{domain}")
        
        # Preferred Chinese lyrics sites
        chinese_lyrics_sites = [
            "mojim.com",
            "kugeci.com",
            "lyrics.kugou.com",
            "music.163.com"
        ]
        
        # Create search query focusing on Chinese lyrics sites
        site_preferences = " OR ".join(f"site:{site}" for site in chinese_lyrics_sites 
                                     if excluded_sites is None or site not in excluded_sites.get_excluded_domains_for_search())
        
        # Build search query with both traditional and simplified Chinese terms
        search_query = f"{query} (歌词 OR 歌詞)"
        if site_preferences:
            search_query = f"({search_query}) ({site_preferences})"
        if exclusions:
            search_query += f" {' '.join(exclusions)}"
        
        logger.info(f"Modified search query: {search_query}")
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=5))
                last_request_time = time()
                
                formatted_results = []
                seen_urls = set()
                
                for result in results:
                    url = _extract_url(result)
                    if not url:
                        continue
                        
                    title = result.get('title', '')
                    
                    # Check URL validity and exclusion
                    if url not in seen_urls and (excluded_sites is None or not excluded_sites.is_site_excluded(url)):
                        # Try to fetch content before adding to results
                        content = await get_page_content(url)
                        if content:
                            logger.info(f"Found result: {title} at {url}")
                            formatted_results.append({
                                "title": title,
                                "url": url
                            })
                            seen_urls.add(url)
                
                if not formatted_results:
                    logger.warning("No non-excluded results found")
                    return [], {
                        "error": SearchError.NO_RESULTS,
                        "message": "No accessible lyrics found. Please try again later."
                    }
                
                logger.info(f"Found {len(formatted_results)} unique, non-excluded URLs")
                return formatted_results[:5], {
                    "success": True,
                    "message": f"Found {len(formatted_results)} results"
                }
                
        except Exception as e:
            return _handle_search_error(e)
                
    except Exception as e:
        logger.error(f"Error in search_web: {str(e)}")
        return [], {
            "error": SearchError.NETWORK_ERROR,
            "message": f"Unexpected error: {str(e)}"
        }

def _extract_url(result: Dict[str, Any]) -> Optional[str]:
    """Extract URL from search result."""
    for key in ['link', 'url', 'href']:
        if key in result and result[key]:
            return result[key]
    return None

def _check_rate_limit() -> bool:
    """Check if we need to rate limit."""
    current_time = time()
    time_since_last = current_time - last_request_time
    return time_since_last < MIN_REQUEST_INTERVAL

def _get_rate_limit_response() -> Tuple[List, Dict]:
    """Get rate limit response."""
    wait_time = MIN_REQUEST_INTERVAL - (time() - last_request_time)
    return [], {
        "error": SearchError.RATE_LIMIT,
        "message": f"Please wait {wait_time:.0f} seconds before trying again.",
        "wait_time": wait_time
    }

def _handle_search_error(e: Exception) -> Tuple[List, Dict]:
    """Handle search errors."""
    if "ratelimit" in str(e).lower():
        return _get_rate_limit_response()
    else:
        logger.error(f"Search error: {str(e)}")
        return [], {
            "error": SearchError.NETWORK_ERROR,
            "message": f"Error performing search: {str(e)}"
        }

def is_lyrics_site(url: str) -> bool:
    """Check if the URL is likely a lyrics website."""
    lyrics_domains = [
        'lyrics', 'lyric', 'musixmatch', 'genius', 'azlyrics',
        '歌词', 'songlyrics', 'metrolyrics', '歌詞',
        'mojim', 'qq', 'xiami', 'kugou'
    ]
    return any(domain in url.lower() for domain in lyrics_domains)