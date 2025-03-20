import aiohttp
import logging
import re
import ssl
import random
import asyncio
from time import time
import hashlib
from .blocked_sites import BlockedSitesTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache configuration
page_cache = {}
CACHE_DURATION = 3600

# Add after other global variables
blocked_sites = BlockedSitesTracker()

def _generate_cache_key(url: str) -> str:
    """Generate a unique cache key for a URL."""
    return hashlib.md5(url.encode()).hexdigest()

def _is_cache_valid(timestamp: float) -> bool:
    """Check if cached result is still valid."""
    return (time() - timestamp) < CACHE_DURATION

async def get_page_content(url: str) -> str:
    """Get and parse webpage content with caching."""
    try:
        logger.info(f"Starting content fetch process for URL: {url}")
        
        # Check if site is blocked
        if blocked_sites.is_site_blocked(url):
            logger.warning(f"Skipping blocked site: {url}")
            return ""
        
        # Check cache first
        cache_key = _generate_cache_key(url)
        if cache_key in page_cache:
            timestamp, content = page_cache[cache_key]
            if _is_cache_valid(timestamp):
                logger.info(f"Cache hit! Returning cached content from {url}")
                return content
        
        # More browser-like headers
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Cookie handling
        cookies = {
            'visited': '1',
            'locale': 'zh-CN',
        }
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, headers=headers, cookies=cookies, timeout=timeout) as session:
            # Try different variations of the URL
            url_variations = [url]
            if 'www.' not in url:
                url_variations.append(url.replace('://', '://www.'))
            if url.startswith('https://'):
                url_variations.append(url.replace('https://', 'http://'))
            
            logger.info(f"Will try the following URL variations: {url_variations}")
            
            for try_url in url_variations:
                try:
                    # Random delay between requests
                    delay = random.uniform(1, 3)  # Random delay between 1-3 seconds
                    logger.info(f"Waiting {delay:.1f} seconds before trying {try_url}")
                    await asyncio.sleep(delay)
                    
                    async with session.get(try_url) as response:
                        logger.info(f"Response status for {try_url}: {response.status}")
                        logger.info(f"Response headers: {dict(response.headers)}")
                        
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"Successfully fetched raw content (size: {len(content)} bytes)")
                            
                            # Clean up the content
                            content = re.sub(r'\s+', ' ', content)
                            content = re.sub(r'[\r\n]+', '\n', content)
                            
                            # Extract Chinese characters and newlines
                            chinese_chars = re.findall(r'[\u4e00-\u9fff]+|\n', content)
                            content = ' '.join(chinese_chars)
                            
                            if content:
                                logger.info(f"Successfully extracted {len(content)} Chinese characters")
                                page_cache[cache_key] = (time(), content)
                                return content.strip()
                            else:
                                logger.warning("No Chinese characters found in content")
                        elif response.status in [403, 500]:
                            logger.warning(f"Access denied or server error. Status: {response.status}")
                            blocked_sites.add_blocked_site(try_url)
                        else:
                            logger.warning(f"Unexpected status code: {response.status}")
                            
                except Exception as e:
                    logger.warning(f"Error fetching {try_url}: {str(e)}")
                    if "SSL" not in str(e):  # Don't block for SSL errors
                        blocked_sites.add_blocked_site(try_url)
            
            logger.error("All URL variations failed. Website may be blocking automated access.")
            blocked_sites.add_blocked_site(url)
            return ""
                    
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return ""