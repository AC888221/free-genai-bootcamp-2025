import json
import logging
import boto3
from botocore.config import Config
from typing import Dict, Any
import os
from .search_web import search_web
from .get_page_content import get_page_content
import re
import asyncio

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
        # Proceed with web search
        search_query = f"{song_name} {artist_name if artist_name else ''} 歌词"
        
        results, status = await search_web(search_query)
        
        if "error" in status:
            return {
                "error": status["message"],
                "wait_required": status.get("wait_time", None)
            }
        
        if not results:
            return {"error": "No results found"}
        
        for result in results:
            content = await get_page_content(result["url"])
            if content and contains_chinese(content):
                # Process lyrics with Bedrock
                prompt = f"""Extract and clean the Chinese lyrics from this content. 
                Remove any non-lyrics content, English translations, or metadata.
                Format the lyrics with proper line breaks.
                
                Content: {content}
                
                Return only the cleaned Chinese lyrics."""
                
                body = json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.7,
                })
                
                response = bedrock_runtime.invoke_model(
                    modelId="anthropic.claude-v2",
                    body=body
                )
                
                response_body = json.loads(response.get('body').read())
                cleaned_lyrics = response_body.get('completion', '').strip()
                
                if contains_chinese(cleaned_lyrics):
                    return {
                        "lyrics": cleaned_lyrics,
                        "artist": artist_name,
                        "vocabulary": []
                    }
        
        return {"error": "No valid Chinese lyrics found in search results"}
        
    except Exception as e:
        logger.error(f"Error getting lyrics: {str(e)}")
        return {"error": str(e)}

def contains_chinese(text: str) -> bool:
    """Check if the text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text)) 