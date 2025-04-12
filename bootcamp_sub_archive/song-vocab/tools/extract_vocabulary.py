import re
import json
import os
import httpx
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Set the Ollama server address from environment variables
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:8008")

async def extract_vocabulary(text: str) -> List[Dict[str, str]]:
    """Extract vocabulary from text using LLM."""
    try:
        logger.info("Starting vocabulary extraction")
        
        # Prepare the prompt with JSON delimiters
        prompt = f"""Extract Chinese vocabulary from the following text and provide the output in JSON format. 
        Return only the JSON content between [START_JSON] and [END_JSON] tags.
        
        For each word, provide:
        - word: The Chinese characters
        - jiantizi: Simplified form
        - pinyin: Pronunciation in pinyin
        - english: English translation
        
        Text: {text}
        
        Format the output exactly like this:
        [START_JSON]
        [
            {{"word": "你好", "jiantizi": "你好", "pinyin": "nǐ hǎo", "english": "hello"}},
            {{"word": "再见", "jiantizi": "再见", "pinyin": "zài jiàn", "english": "goodbye"}}
        ]
        [END_JSON]
        """
        
        logger.info("Sending request to LLM.")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_API_BASE}/api/generate",
                json={"model": "phi3:3.8b", "prompt": prompt},
                timeout=30.0
            )
            
            response.raise_for_status()
            response_text = response.text
            
            logger.debug(f"Raw LLM response: {response_text}")
            
            # Extract content between JSON tags
            start_idx = response_text.find("[START_JSON]")
            end_idx = response_text.find("[END_JSON]")
            
            if start_idx == -1 or end_idx == -1:
                logger.error("JSON tags not found in response")
                # Log a sample of the response for debugging
                capped_content = response_text[:500] + '...' if len(response_text) > 500 else response_text
                logger.debug(f"Response content (capped): {capped_content}")
                return fallback_extraction(text)
            
            # Extract and clean the JSON content
            json_str = response_text[start_idx + len("[START_JSON]"):end_idx].strip()
            
            try:
                data = json.loads(json_str)
                if not isinstance(data, list):
                    logger.error("LLM response is not a list")
                    return fallback_extraction(text)
                
                # Validate and clean each vocabulary item
                validated_vocab = []
                for item in data:
                    if isinstance(item, dict) and all(k in item for k in ["word", "jiantizi", "pinyin", "english"]):
                        # Clean and validate each field
                        cleaned_item = {
                            "word": str(item["word"]).strip(),
                            "jiantizi": str(item["jiantizi"]).strip(),
                            "pinyin": str(item["pinyin"]).strip(),
                            "english": str(item["english"]).strip()
                        }
                        # Only include items that have actual Chinese characters
                        if contains_chinese(cleaned_item["word"]):
                            validated_vocab.append(cleaned_item)
                
                if not validated_vocab:
                    logger.warning("No valid vocabulary items found in LLM response")
                    return fallback_extraction(text)
                
                logger.info(f"Successfully extracted {len(validated_vocab)} vocabulary items")
                return validated_vocab
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.debug(f"Failed JSON: {json_str}")
                return fallback_extraction(text)
                
    except httpx.TimeoutException as e:
        logger.error(f"Request timed out: {str(e)}")
        return fallback_extraction(text)
    except httpx.ConnectError as e:
        logger.error(f"Connection error: {str(e)}")
        return fallback_extraction(text)
    except Exception as e:
        logger.error(f"Error in extract_vocabulary: {str(e)}")
        return fallback_extraction(text)

def clean_chinese_text(text: str) -> str:
    """Clean the text to focus on Chinese content."""
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove markdown formatting
    text = re.sub(r'\[.*?\]|\(.*?\)|\*\*|__|\*|_|##+', '', text)
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def contains_chinese(text: str) -> bool:
    """Check if the text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def fallback_extraction(text: str) -> List[Dict[str, Any]]:
    """Simple fallback method to extract Chinese words and characters."""
    # First try to extract multi-character words (2-4 characters)
    words = []
    chinese_pattern = r'[\u4e00-\u9fff]{2,4}'
    multi_char_words = re.findall(chinese_pattern, text)
    
    # Then extract single characters
    single_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Combine both, prioritizing multi-character words
    all_words = list(dict.fromkeys(multi_char_words + list(single_chars)))
    
    # Create vocabulary items
    return [
        {
            "word": word,
            "jiantizi": word,  # Simplified form (same as original in this fallback)
            "pinyin": "unknown",  # We don't have pinyin in this fallback
            "english": "unknown"  # We don't have translation in this fallback
        }
        for word in all_words[:30]  # Limit to 30 items
    ]