import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import boto3
from botocore.config import Config
from tools.search_web import search_web
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary, fallback_extraction
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
    
    def _contains_chinese(self, content: str) -> bool:
        """Check if content contains Chinese characters."""
        return any('\u4e00' <= char <= '\u9fff' for char in content)
    
    async def validate_chinese_content(self, content: str) -> Tuple[bool, str]:
        """Validate if content contains sufficient Chinese characters."""
        chinese_char_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        if chinese_char_count < 10:  # Arbitrary threshold
            return False, "Insufficient Chinese content found"
        return True, ""
    
    async def get_lyrics(self, song_name: str, artist_name: str = None):
        # 1. Search for lyrics
        results, status = await search_web(f"{song_name} {artist_name} 歌词")
        
        # 2. Get content from results
        for result in results:
            content = await get_page_content(result["url"])
            if content and self._contains_chinese(content):
                # Return content directly instead of cleaning
                # We'll clean at the run level if needed
                return content
        
        return None

    async def extract_vocabulary(self, text: str) -> List[Dict[str, Any]]:
        """Extract vocabulary from text using imported function."""
        try:
            self.logger.info("Extracting vocabulary")
            vocabulary = await extract_vocabulary(text)
            if not vocabulary:
                self.logger.warning("No vocabulary extracted, using fallback")
                vocabulary = fallback_extraction(text)
            return vocabulary
        except Exception as e:
            self.logger.error(f"Error in extract_vocabulary: {str(e)}")
            return fallback_extraction(text)
    
    async def run(self, song_name: str, artist: str = "") -> Dict[str, Any]:
        try:
            session_id = generate_song_id(artist, song_name)
            self.logger.info(f"Starting session {session_id}")
            
            # Get lyrics
            lyrics_result = await self.get_lyrics(song_name, artist)
            
            if lyrics_result is None:
                raise Exception("No valid Chinese lyrics found")
            
            # Use lyrics as-is without cleaning
            cleaned_lyrics = lyrics_result
            initial_vocabulary = await self.extract_vocabulary(cleaned_lyrics)
            
            result = {
                "session_id": session_id,
                "lyrics": cleaned_lyrics,
                "vocabulary": initial_vocabulary,
                "metadata": {
                    "song_name": song_name,
                    "artist": artist
                }
            }
            
            # Save to database using a new connection
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO songs (song_id, title, artist, lyrics, vocabulary) VALUES (?, ?, ?, ?, ?)",
                    (session_id, song_name, artist, cleaned_lyrics, json.dumps(initial_vocabulary))
                )
                conn.commit()
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error in run: {error_msg}")
            return {
                "error": error_msg,
                "session_id": session_id if 'session_id' in locals() else "",
                "lyrics": "",
                "vocabulary": []
            }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the agent's interaction history."""
        return self.history