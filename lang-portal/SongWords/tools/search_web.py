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
            # Log the search attempt
            logger.info("Initializing DuckDuckGo search")
            
            try:
                # Get raw results and convert to list immediately to catch any iterator errors
                raw_results = list(ddgs.text(query, max_results=10))
                logger.info(f"Received {len(raw_results)} raw results")
                
                # Log the first raw result to see its structure
                if raw_results:
                    logger.info(f"First raw result structure: {json.dumps(raw_results[0], ensure_ascii=False, indent=2)}")
                
                if raw_results:
                    formatted_results = []
                    for i, result in enumerate(raw_results):
                        try:
                            # Log each result's keys
                            logger.info(f"Result {i} keys: {list(result.keys())}")
                            
                            # Try multiple possible URL fields
                            url = None
                            for url_field in ['href', 'url', 'link', 'source']:
                                url = result.get(url_field)
                                if url:
                                    logger.info(f"Found URL in field '{url_field}': {url}")
                                    break
                            
                            if not url:
                                logger.warning(f"No URL found in result {i}")
                                continue
                            
                            title = result.get('title', '')
                            logger.info(f"Processing result {i}: title='{title}', url='{url}'")
                            
                            formatted_results.append({
                                "title": title,
                                "url": url
                            })
                            
                        except Exception as e:
                            logger.error(f"Error processing result {i}: {str(e)}")
                            logger.error(f"Problematic result: {json.dumps(result, ensure_ascii=False, indent=2)}")
                            continue
                    
                    if formatted_results:
                        logger.info(f"Successfully formatted {len(formatted_results)} results")
                        return formatted_results
                    else:
                        logger.warning("No results could be formatted properly")
                        return []
                else:
                    logger.warning("DuckDuckGo returned no results")
                    return []
                    
            except Exception as e:
                logger.error(f"Error during DuckDuckGo search: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Error in search_web: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to search web: {str(e)}")