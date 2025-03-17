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
        """Enhanced workflow with better error handling and HSK level support."""
        try:
            session_id = generate_song_id(artist, song_name)
            self.logger.info(f"Starting session {session_id}")
            
            # Search multiple sources
            search_queries = [
                f"{song_name} {artist} 歌词",
                f"{song_name} lyrics chinese",
                f"{artist} {song_name} 中文歌词"
            ]
            
            content = None
            source_url = None
            
            for query in search_queries:
                search_results = await search_web(query)
                
                for result in search_results[:3]:  # Try first 3 results
                    page_content = await get_page_content(result['url'])
                    if page_content:
                        is_valid, error = await self.validate_chinese_content(page_content)
                        if is_valid:
                            content = page_content
                            source_url = result['url']
                            break
                
                if content:
                    break
            
            if not content:
                raise Exception("No valid Chinese lyrics found")
            
            # Clean and process lyrics
            cleaned_lyrics = await self.clean_lyrics(content)
            vocabulary = await self.extract_vocabulary(cleaned_lyrics, hsk_level)
            
            result = {
                "session_id": session_id,
                "lyrics": cleaned_lyrics,
                "vocabulary": vocabulary,
                "source": source_url,
                "metadata": {
                    "song_name": song_name,
                    "artist": artist,
                    "hsk_level": hsk_level
                }
            }
            
            # Save to database
            self.db.save_song(artist, song_name, cleaned_lyrics, vocabulary)
            
            # Store in history
            self.history.append(result)
            
            return result
            
        except Exception as e:
            error_result = {
                "session_id": generate_song_id(artist, song_name),
                "lyrics": "",
                "vocabulary": [],
                "source": "",
                "error": str(e),
                "metadata": {
                    "song_name": song_name,
                    "artist": artist,
                    "hsk_level": hsk_level
                }
            }
            self.history.append(error_result)
            return error_result
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the agent's interaction history."""
        return self.history