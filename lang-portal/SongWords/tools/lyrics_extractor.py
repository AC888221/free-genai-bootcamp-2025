import json
import logging
import boto3
from botocore.config import Config
from typing import Dict, Any
import os
from .search_web import search_web
from .get_page_content import get_page_content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    config=Config(
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
)

async def get_lyrics(song_name: str, artist_name: str = None) -> Dict[str, Any]:
    """Extract lyrics using web search and Bedrock for analysis."""
    try:
        # Construct search query
        search_query = f"{song_name} {artist_name if artist_name else ''} lyrics 歌词"
        
        # Search for lyrics
        search_results = await search_web(search_query)
        
        # Try to get content from each result until we find lyrics
        lyrics_content = None
        for result in search_results:
            content = await get_page_content(result["url"])
            if content and "歌词" in content:
                lyrics_content = content
                break
        
        if not lyrics_content:
            return {"error": "Could not find lyrics"}
        
        # Use Bedrock to analyze the lyrics
        prompt = f"""Analyze these Chinese lyrics and provide:
        1. The cleaned lyrics in Chinese
        2. A vocabulary list with pinyin and translations
        
        Raw content:
        {lyrics_content}
        
        Return in this JSON format:
        {{"lyrics": "完整歌词...", "vocabulary": [{{"word": "你好", "pinyin": "nǐ hǎo", "english": "hello"}}]}}
        """
        
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
            "temperature": 0.7,
        })
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-v2",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        return {
            "lyrics": response_body.get("lyrics", ""),
            "vocabulary": response_body.get("vocabulary", [])
        }
    except Exception as e:
        logger.error(f"Error getting lyrics: {str(e)}")
        return {"error": str(e)} 