import httpx
import logging
from html2text import HTML2Text
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_page_content(url: str) -> Optional[str]:
    """Get and parse content from a webpage."""
    try:
        logger.info(f"Fetching content from: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Convert HTML to text
            h = HTML2Text()
            h.ignore_links = False
            content = h.handle(response.text)
            
            # Truncate if content is too long
            if len(content) > 4000:
                logger.info("Content truncated to 4000 characters")
                content = content[:4000]
            
            if content:
                logger.info(f"Successfully extracted {len(content)} characters of content")
                return content
            else:
                logger.warning("No content found in webpage")
                return None
                
    except Exception as e:
        logger.error(f"Error fetching page content: {str(e)}")
        raise Exception(f"Failed to get page content: {str(e)}")