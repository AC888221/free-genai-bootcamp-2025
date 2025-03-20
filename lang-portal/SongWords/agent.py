import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import boto3
from botocore.config import Config
from tools.search_web import search_web
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary
from tools.generate_song_id import generate_song_id
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LyricsAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.history: List[Dict[str, Any]] = []
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            config=Config(
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        # Add database initialization
        self.db = Database()
        self.db.create_tables()
    
    async def get_lyrics(self, song_name: str, artist_name: str = None):
        # 1. Search for lyrics
        results, status = await search_web(f"{song_name} {artist_name} 歌词")
        
        # 2. Get content from results
        for result in results:
            content = await get_page_content(result["url"])
            if content:
                return content
        
        return None

    async def process_lyrics(self, lyrics: str) -> Dict[str, Any]:
        """Process lyrics text and extract vocabulary."""
        try:
            # Use extract_vocabulary which already handles text processing
            simplified_text, vocabulary = await extract_vocabulary(lyrics)
            
            if not simplified_text:
                return {
                    "success": False,
                    "error": "No valid Chinese text found in lyrics"
                }
            
            return {
                "success": True,
                "lyrics": simplified_text,
                "vocabulary": vocabulary,
                "was_converted": simplified_text != lyrics
            }
        except Exception as e:
            self.logger.error(f"Error processing lyrics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }