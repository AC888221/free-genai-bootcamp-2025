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
from config import AWS_CONFIG, MODEL_CONFIG, DB_PATH, LOG_CONFIG

# Configure logging
logging.basicConfig(**LOG_CONFIG)
logger = logging.getLogger(__name__)

class LyricsAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.history: List[Dict[str, Any]] = []
        # Initialize Bedrock client with configuration values
        self.bedrock_runtime = boto3.client(
            service_name=AWS_CONFIG["service"],
            config=Config(
                region_name=AWS_CONFIG["region"],
                retries=AWS_CONFIG["retries"]
            )
        )
        # Initialize database with configured path
        self.db = Database()
        self.db.db_path = DB_PATH
        self.db.create_tables()
    
    async def run(self, song_name: str, artist_name: str = None) -> Dict[str, Any]:
        """
        Main method to search for a song and process its lyrics.
        
        Args:
            song_name (str): Name of the song to search for
            artist_name (str, optional): Name of the artist
            
        Returns:
            Dict[str, Any]: Results containing lyrics and vocabulary
        """
        try:
            self.logger.info(f"Agent running search for '{song_name}' by '{artist_name}'")
            
            # Get the lyrics
            lyrics = await self.get_lyrics(song_name, artist_name)
            if not lyrics:
                return {"error": "Could not find lyrics for this song"}
            
            # Process the lyrics with configured temperature and max_tokens
            result = await self.process_lyrics(lyrics)
            
            # Store in database if successful
            if result.get("success", False):
                # Generate song ID explicitly
                song_id = generate_song_id(artist_name or "", song_name)
                
                # Save to database with the generated ID
                self.db.save_song(
                    song_id=song_id,
                    artist=artist_name or "",
                    title=song_name,
                    lyrics=result["lyrics"],
                    vocabulary=result["vocabulary"]
                )
                
                # Save to history with source='search'
                try:
                    self.db.save_to_history(
                        query=song_name,
                        lyrics=lyrics,
                        vocabulary=str(result["vocabulary"]),
                        source='search'
                    )
                except Exception as e:
                    logger.error(f"Error saving to history: {str(e)}")
            
            return {
                "lyrics": result.get("lyrics", ""),
                "vocabulary": result.get("vocabulary", []),
                "success": result.get("success", False),
                "error": result.get("error", None),
                "song_id": song_id if result.get("success", False) else None
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent.run: {str(e)}")
            return {"error": f"An unexpected error occurred: {str(e)}"}

    async def get_lyrics(self, song_name: str, artist_name: str = None):
        # Search for lyrics using configured temperature
        results, status = await search_web(
            f"{song_name} {artist_name} 歌词"
        )
        
        # Get content from results with configured max_tokens
        for result in results:
            content = await get_page_content(
                result["url"]
            )
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