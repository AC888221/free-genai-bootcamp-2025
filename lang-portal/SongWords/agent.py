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
from tools.lyrics_extractor import get_lyrics

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
    
    async def validate_chinese_content(self, content: str) -> Tuple[bool, str]:
        """Validate if content contains sufficient Chinese characters."""
        chinese_char_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        if chinese_char_count < 10:  # Arbitrary threshold
            return False, "Insufficient Chinese content found"
        return True, ""
    
    async def clean_lyrics(self, raw_lyrics: str) -> str:
        """Use Bedrock to clean and format lyrics."""
        try:
            prompt = f"""Clean and format these Chinese lyrics. Remove any English translations, 
            advertisements, or irrelevant content. Keep only the Chinese lyrics.

            Raw lyrics:
            {raw_lyrics}

            Return only the cleaned Chinese lyrics."""
            
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 1000,
                "temperature": 0.3,  # Lower temperature for more consistent cleaning
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('completion', '').strip()
        except Exception as e:
            self.logger.error(f"Error cleaning lyrics: {str(e)}")
            return raw_lyrics
    
    async def extract_vocabulary(self, text: str, hsk_level: str = "HSK 1") -> List[Dict[str, Any]]:
        """Extract vocabulary from text using Bedrock with HSK level consideration."""
        try:
            self.logger.info(f"Extracting vocabulary (HSK level: {hsk_level})")
            prompt = f"""Extract Chinese vocabulary from this text. 
            Focus on {hsk_level} level words where possible.
            Include only words that are appropriate for this level.
            
            Text: {text}
            
            Return in JSON format:
            [
                {{"word": "你好", "pinyin": "nǐ hǎo", "english": "hello", "hsk_level": "1"}},
                {{"word": "再见", "pinyin": "zài jiàn", "english": "goodbye", "hsk_level": "1"}}
            ]
            """
            
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 1000,
                "temperature": 0.7,
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            vocabulary = json.loads(response_body.get('completion', '[]'))
            
            if not vocabulary:
                self.logger.warning("No vocabulary extracted, using fallback")
                vocabulary = fallback_extraction(text)
            return vocabulary
        except Exception as e:
            self.logger.error(f"Error in extract_vocabulary: {str(e)}")
            return fallback_extraction(text)
    
    async def run(self, song_name: str, artist: str = "", hsk_level: str = "HSK 1") -> Dict[str, Any]:
        try:
            session_id = generate_song_id(artist, song_name)
            self.logger.info(f"Starting session {session_id}")
            
            # Get lyrics
            lyrics_result = await get_lyrics(song_name, artist)
            
            if "error" in lyrics_result:
                raise Exception(lyrics_result["error"])
            
            cleaned_lyrics = lyrics_result.get("lyrics", "")
            initial_vocabulary = lyrics_result.get("vocabulary", [])
            
            # Extract additional vocabulary if needed
            if not initial_vocabulary:
                vocabulary = await extract_vocabulary(cleaned_lyrics)
            else:
                vocabulary = initial_vocabulary
            
            result = {
                "session_id": session_id,
                "lyrics": cleaned_lyrics,
                "vocabulary": vocabulary,
                "metadata": {
                    "song_name": song_name,
                    "artist": artist,
                    "hsk_level": hsk_level
                }
            }
            
            # Save to database using a new connection
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO songs (id, title, artist, lyrics, vocabulary) VALUES (?, ?, ?, ?, ?)",
                    (session_id, song_name, artist, cleaned_lyrics, json.dumps(vocabulary))
                )
                conn.commit()
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error in run: {error_msg}")
            return {
                "error": error_msg,
                "session_id": session_id,
                "lyrics": "",
                "vocabulary": []
            }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the agent's interaction history."""
        return self.history