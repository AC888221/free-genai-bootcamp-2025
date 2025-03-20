import json
import os
import sys
import asyncio
import logging
import pytest
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import LyricsAgent
from database import Database
from tools.text_processing import clean_chinese_text, contains_chinese, process_chinese_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def db():
    """Create a test database instance."""
    db = Database()
    db.db_path = "test_songwords.db"  # Use a test database file
    db.create_tables()
    yield db
    # Cleanup
    db.close()
    if os.path.exists(db.db_path):
        os.remove(db.db_path)

@pytest.fixture
async def agent(db):
    """Create a test agent instance with test database."""
    return LyricsAgent(db=db)

@pytest.mark.asyncio
async def test_text_processing():
    """Test Chinese text processing functions."""
    # Test Chinese content detection
    valid_text = "你好世界"
    assert contains_chinese(valid_text) == True
    
    # Test non-Chinese content
    invalid_text = "Hello world"
    assert contains_chinese(invalid_text) == False
    
    # Test text cleaning
    raw_lyrics = """
    你好 (Hello)
    世界 (World)
    [00:01] Some timestamp
    https://example.com
    """
    
    cleaned = clean_chinese_text(raw_lyrics)
    assert "Hello" not in cleaned
    assert "World" not in cleaned
    assert "[00:01]" not in cleaned
    assert "https://" not in cleaned
    assert "你好" in cleaned
    assert "世界" in cleaned
    
    # Test full processing
    processed_text, was_converted = process_chinese_text(raw_lyrics)
    assert contains_chinese(processed_text)
    assert isinstance(was_converted, bool)

@pytest.mark.asyncio
async def test_extract_vocabulary():
    """Test vocabulary extraction."""
    agent = LyricsAgent()
    
    text = "你好世界"
    result = await agent.process_lyrics(text)  # Use process_lyrics method
    
    assert "vocabulary" in result
    vocabulary = result["vocabulary"]
    assert isinstance(vocabulary, list)
    assert len(vocabulary) > 0
    for item in vocabulary:
        assert "jiantizi" in item
        assert "pinyin" in item
        assert "english" in item

@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test the complete agent workflow."""
    agent = LyricsAgent()  # No db argument
    
    result = await agent.run("月亮代表我的心", "邓丽君")
    
    assert "lyrics" in result
    assert "vocabulary" in result
    assert "success" in result
    assert len(result["vocabulary"]) > 0
    
    # Test that it was saved to history with correct source
    history = agent.db.get_history()  # Access the agent's internal db
    assert len(history) > 0
    latest = history[0]
    assert latest[4] == 'search'  # Check source field

@pytest.mark.asyncio
async def test_database_operations(db):
    """Test database operations."""
    # Clear the history to ensure a clean state
    db.clear_history()  # Assuming you have a method to clear history

    # Test saving search result
    db.save_to_history("Test Song", "Test Lyrics", "[{'word': 'test'}]", source='search')
    
    # Test saving manual input
    db.save_to_history("Manual Input", "Test Text", "[{'word': 'test'}]", source='input')
    
    # Test retrieving history
    history = db.get_history()
    assert len(history) == 2
    
    # Test getting most recent search
    search_result = db.get_most_recent_search(source='search')
    assert search_result is not None
    assert search_result[0] == "Test Song"
    
    # Test getting most recent input
    input_result = db.get_most_recent_search(source='input')
    assert input_result is not None
    assert input_result[0] == "Manual Input"

@pytest.mark.asyncio
async def test_thread_safety(db):
    """Test database thread safety."""
    # Clear the history to ensure a clean state
    db.clear_history()  # Assuming you have a method to clear history

    async def concurrent_operation(i):
        db.save_to_history(f"Test {i}", "Lyrics", "[]", source='search')
    
    # Run multiple operations concurrently
    await asyncio.gather(*[concurrent_operation(i) for i in range(5)])
    
    # Check that all operations were saved
    history = db.get_history()
    assert len(history) == 5

async def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")
    
    # Create test database
    db = Database()
    db.db_path = "test_songwords.db"
    db.create_tables()
    
    try:
        # Run tests
        await test_text_processing()
        await test_extract_vocabulary()
        await test_full_agent_workflow()
        await test_database_operations(db)
        await test_thread_safety(db)
        
        logger.info("All tests completed successfully!")
        return True
        
    finally:
        # Cleanup
        db.close()
        if os.path.exists(db.db_path):
            os.remove(db.db_path)

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)