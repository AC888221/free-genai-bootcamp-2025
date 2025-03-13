import aiohttp
import asyncio
import json
import time
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_server_connection(session, base_url: str) -> bool:
    """Test if the server is running and accessible."""
    max_retries = 5
    for i in range(max_retries):
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    logger.info("Server is running")
                    return True
        except aiohttp.ClientError as e:
            logger.warning(f"Server not ready (attempt {i+1}/{max_retries}): {str(e)}")
        await asyncio.sleep(2)
    
    logger.error("Server did not start in time")
    return False

async def test_agent_endpoint(session, base_url: str) -> bool:
    """Test the /api/agent endpoint."""
    try:
        logger.info("\nTesting /api/agent endpoint...")
        
        payload = {
            "message_request": "月亮代表我的心",
            "artist_name": "邓丽君"
        }
        
        async with session.post(
            f"{base_url}/api/agent",
            json=payload,
            timeout=30
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info("Success! Sample of lyrics:")
                logger.info(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
                logger.info(f"Number of vocabulary items: {len(result['vocabulary'])}")
                return True
            else:
                error_text = await response.text()
                logger.error(f"Error {response.status}: {error_text}")
                return False
    except Exception as e:
        logger.error(f"Error testing agent endpoint: {str(e)}")
        return False

async def test_vocabulary_endpoint(session, base_url: str) -> bool:
    """Test the /api/get_vocabulary endpoint."""
    try:
        logger.info("\nTesting /api/get_vocabulary endpoint...")
        
        payload = {
            "text": "月亮代表我的心\n你问我爱你有多深\n我爱你有几分"
        }
        
        async with session.post(
            f"{base_url}/api/get_vocabulary",
            json=payload,
            timeout=30
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info("Success! Sample of vocabulary:")
                for i, vocab in enumerate(result["vocabulary"][:3]):
                    logger.info(f"{i+1}. {vocab['word']} - {vocab['pinyin']} - {vocab['english']}")
                return True
            else:
                error_text = await response.text()
                logger.error(f"Error {response.status}: {error_text}")
                return False
    except Exception as e:
        logger.error(f"Error testing vocabulary endpoint: {str(e)}")
        return False

async def test_api_endpoints():
    """Test all API endpoints."""
    base_url = "http://localhost:8000"
    logger.info("Starting API tests...")
    
    async with aiohttp.ClientSession() as session:
        # Test server connection
        if not await test_server_connection(session, base_url):
            return False
            
        # Test individual endpoints
        agent_success = await test_agent_endpoint(session, base_url)
        vocab_success = await test_vocabulary_endpoint(session, base_url)
        
        # Report results
        logger.info("\n=== API TEST RESULTS ===")
        logger.info(f"Agent Endpoint: {'✓' if agent_success else '✗'}")
        logger.info(f"Vocabulary Endpoint: {'✓' if vocab_success else '✗'}")
        
        success = all([agent_success, vocab_success])
        logger.info(f"\nOverall API test success: {'✓' if success else '✗'}")
        return success

if __name__ == "__main__":
    success = asyncio.run(test_api_endpoints())
    sys.exit(0 if success else 1)