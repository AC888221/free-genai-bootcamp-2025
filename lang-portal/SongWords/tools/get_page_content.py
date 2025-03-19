import aiohttp
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_page_content(url: str) -> str:
    """Get and parse webpage content."""
    try:
        logger.info(f"Attempting to fetch content from: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Clean up the content
                    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
                    content = re.sub(r'[\r\n]+', '\n', content)  # Normalize newlines
                    
                    # Extract Chinese characters and newlines
                    chinese_chars = re.findall(r'[\u4e00-\u9fff]+|\n', content)
                    content = ' '.join(chinese_chars)
                    
                    if content:
                        logger.info(f"Successfully extracted {len(content)} characters from {url}")
                    else:
                        logger.warning(f"No Chinese content found in {url}")
                    
                    return content.strip()
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return ""