import json
import os
import sys
import asyncio
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import LyricsAgent
from tools.search_web import search_web
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search_web():
    """Test the web search functionality."""
    logger.info("\nTesting web search...")
    
    search_query = "月亮代表我的心 lyrics 邓丽君"
    try:
        results = await search_web(search_query)
        if results and len(results) > 0:
            logger.info(f"Found {len(results)} search results")
            logger.info(f"First result: {results[0]['url']}")
            return True
        else:
            logger.error("No search results found")
            return False
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        return False

async def test_get_page_content():
    """Test the page content extraction."""
    logger.info("\nTesting page content extraction...")
    
    # First get a URL from search
    search_results = await search_web("月亮代表我的心 lyrics 邓丽君")
    if not search_results:
        logger.error("No search results to test content extraction")
        return False
    
    try:
        lyrics_url = search_results[0]['url']
        logger.info(f"Fetching content from: {lyrics_url}")
        content = await get_page_content(lyrics_url)
        
        if content:
            logger.info(f"Successfully extracted content ({len(content)} characters)")
            logger.info("Sample of content:")
            logger.info(content[:200] + "..." if len(content) > 200 else content)
            return True
        else:
            logger.error("No content extracted")
            return False
    except Exception as e:
        logger.error(f"Error in content extraction: {str(e)}")
        return False

async def test_vocabulary_extraction():
    """Test vocabulary extraction with a sample text."""
    logger.info("\nTesting vocabulary extraction...")
    
    # Sample Chinese text
    sample_text = """
    月亮代表我的心
    你问我爱你有多深
    我爱你有几分
    你去想一想
    你去看一看
    月亮代表我的心
    """
    
    try:
        vocabulary = await extract_vocabulary(sample_text)
        
        logger.info("\n=== EXTRACTED VOCABULARY ===")
        for i, vocab in enumerate(vocabulary[:5]):  # Show first 5 items
            logger.info(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        logger.info(f"\nTotal vocabulary items: {len(vocabulary)}")
        return True
    except Exception as e:
        logger.error(f"Error testing vocabulary extraction: {str(e)}")
        return False

async def test_full_agent():
    """Test the complete agent workflow."""
    logger.info("\nTesting full agent workflow...")
    
    agent = LyricsAgent()
    song_request = "月亮代表我的心"
    artist_name = "邓丽君"
    
    logger.info(f"Processing song: {song_request} by {artist_name}")
    
    try:
        result = await agent.run(song_request, artist_name)
        
        logger.info("\n=== LYRICS ===")
        logger.info(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
        
        logger.info("\n=== VOCABULARY SAMPLE ===")
        for i, vocab in enumerate(result["vocabulary"][:5]):
            logger.info(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        logger.info(f"\nTotal vocabulary items: {len(result['vocabulary'])}")
        
        # Save results
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{song_request}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nResults saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error in full agent test: {str(e)}")
        return False

async def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")
    
    # Run tests in sequence
    search_success = await test_search_web()
    content_success = await test_get_page_content()
    vocab_success = await test_vocabulary_extraction()
    agent_success = await test_full_agent()
    
    # Report results
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Web Search: {'✓' if search_success else '✗'}")
    logger.info(f"Content Extraction: {'✓' if content_success else '✗'}")
    logger.info(f"Vocabulary Extraction: {'✓' if vocab_success else '✗'}")
    logger.info(f"Full Agent: {'✓' if agent_success else '✗'}")
    
    success = all([search_success, content_success, vocab_success, agent_success])
    logger.info(f"\nOverall test success: {'✓' if success else '✗'}")
    return success

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)