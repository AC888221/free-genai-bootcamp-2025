import json
import os
import sys
import asyncio
import logging
import pytest
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import LyricsAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
async def agent():
    """Create a test agent instance."""
    return LyricsAgent()

@pytest.mark.asyncio
async def test_validate_chinese_content():
    """Test Chinese content validation."""
    agent = LyricsAgent()
    
    # Test valid Chinese content
    valid_text = "你好世界"
    is_valid, error = await agent.validate_chinese_content(valid_text)
    assert is_valid == True
    assert error == ""
    
    # Test invalid content
    invalid_text = "Hello world"
    is_valid, error = await agent.validate_chinese_content(invalid_text)
    assert is_valid == False
    assert "Insufficient Chinese content" in error

@pytest.mark.asyncio
async def test_clean_lyrics():
    """Test lyrics cleaning."""
    agent = LyricsAgent()
    
    raw_lyrics = """
    你好 (Hello)
    世界 (World)
    [00:01] Some timestamp
    """
    
    cleaned = await agent.clean_lyrics(raw_lyrics)
    assert "Hello" not in cleaned
    assert "World" not in cleaned
    assert "[00:01]" not in cleaned
    assert "你好" in cleaned
    assert "世界" in cleaned

@pytest.mark.asyncio
async def test_extract_vocabulary():
    """Test vocabulary extraction."""
    agent = LyricsAgent()
    
    text = "你好世界"
    vocabulary = await agent.extract_vocabulary(text)
    
    assert isinstance(vocabulary, list)
    assert len(vocabulary) > 0
    for item in vocabulary:
        assert "word" in item
        assert "pinyin" in item
        assert "english" in item
        assert "hsk_level" in item

@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test the complete agent workflow."""
    agent = LyricsAgent()
    
    result = await agent.run("月亮代表我的心", "邓丽君")
    
    assert "session_id" in result
    assert "lyrics" in result
    assert "vocabulary" in result
    assert "source" in result
    assert "metadata" in result
    assert len(result["vocabulary"]) > 0

@pytest.mark.asyncio
async def test_error_handling():
    """Test agent error handling."""
    agent = LyricsAgent()
    
    # Test with invalid input
    result = await agent.run("", "")
    assert "error" in result
    
    # Test with non-existent song
    result = await agent.run("ThisSongDoesNotExist12345", "NonExistentArtist")
    assert "error" in result

async def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")
    
    # Run tests
    await test_validate_chinese_content()
    await test_clean_lyrics()
    await test_extract_vocabulary()
    await test_full_agent_workflow()
    await test_error_handling()
    
    logger.info("All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)