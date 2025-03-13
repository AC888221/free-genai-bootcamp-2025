import os
import json
import logging
from typing import Dict, List, Optional, Any
from tools.search_web import search_web
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary, fallback_extraction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LyricsAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def extract_vocabulary(self, text: str) -> List[Dict[str, Any]]:
        """Extract vocabulary from the given text."""
        try:
            self.logger.info("Extracting vocabulary from text")
            vocabulary = await extract_vocabulary(text)
            if not vocabulary:
                self.logger.warning("No vocabulary extracted, using fallback")
                vocabulary = fallback_extraction(text)
            return vocabulary
        except Exception as e:
            self.logger.error(f"Error in extract_vocabulary: {str(e)}")
            return fallback_extraction(text)
        
    async def run(self, song_name: str, artist: str = "") -> Dict[str, Any]:
        """
        Run the full lyrics and vocabulary extraction workflow.
        
        Args:
            song_name: Name of the song
            artist: Optional artist name
            
        Returns:
            Dict containing lyrics and vocabulary
        """
        try:
            logger.info(f"Searching for lyrics with query: {song_name} lyrics {artist}")
            
            # Search for lyrics
            search_results = await search_web(f"{song_name} lyrics {artist}")
            if not search_results:
                raise Exception("No search results found")
            
            # Get the first result's content
            first_result = search_results[0]
            logger.info(f"Fetching lyrics from: {first_result['url']}")
            
            content = await get_page_content(first_result['url'])
            if not content:
                raise Exception("Failed to fetch page content")
            
            # Extract vocabulary
            logger.info("Extracting vocabulary from lyrics")
            try:
                logger.info("Extracting vocabulary from text")
                vocabulary = await self.extract_vocabulary(content)
                if not vocabulary:
                    logger.warning("No vocabulary extracted, using fallback")
                    vocabulary = fallback_extraction(content)
            except Exception as e:
                logger.error(f"Error in extract_vocabulary: {str(e)}")
                logger.info("Using fallback vocabulary extraction")
                vocabulary = fallback_extraction(content)
            
            return {
                "lyrics": content,
                "vocabulary": vocabulary,
                "source": first_result['url']
            }
            
        except Exception as e:
            logger.error(f"Error in agent.run: {str(e)}")
            # Return a partial result with what we have
            return {
                "lyrics": "",
                "vocabulary": [],
                "source": "",
                "error": str(e)
            }