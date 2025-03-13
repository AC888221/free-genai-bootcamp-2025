import re
import json
import os
import httpx
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Load environment variables from .env file
load_dotenv()

# Set the Ollama server address from environment variables
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:8008")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def extract_vocabulary(text: str) -> List[Dict[str, Any]]:
    """
    Extract vocabulary from Chinese (Putonghua) text.
    
    Args:
        text (str): The text to extract vocabulary from
        
    Returns:
        List[Dict[str, Any]]: A list of vocabulary items with word, jiantizi, pinyin, and English translation
    """
    logging.info("Starting vocabulary extraction.")
    
    system_prompt = """
    You are a Chinese language vocabulary extractor. Your task is to:
    
    1. Identify unique Chinese words and characters in the given text
    2. For each word, provide:
       - word: The original Chinese word
       - jiantizi: The simplified Chinese form
       - pinyin: The pinyin romanization with tone marks
       - english: The English translation
    
    Return the results as a JSON array containing objects with these four fields.
    Focus on words that would be valuable for a Chinese language learner.
    Ignore common words like pronouns, conjunctions, and particles unless they're important.
    Limit to a maximum of 30 vocabulary items.
    """
    
    cleaned_text = clean_chinese_text(text)
    logging.debug(f"Cleaned text: {cleaned_text[:100]}...")  # Log the first 100 characters of the cleaned text
    
    if not contains_chinese(cleaned_text):
        logging.warning("No Chinese characters found in the text.")
        return []
    
    try:
        logging.info("Sending request to LLM.")
        async with httpx.AsyncClient(base_url=OLLAMA_API_BASE) as client:
            response = await client.post(
                "/api/generate",
                json={
                    "model": "Phi-3-mini-4k-instruct",
                    "prompt": f"Extract vocabulary from the following text:\n\n{cleaned_text[:5000]}",
                    "stream": False
                }
            )
            response.raise_for_status()
            response_content = response.json().get("message", {}).get("content", "")
            logging.debug(f"Response content: {response_content[:100]}...")  # Log the first 100 characters of the response
            
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_content
            
            try:
                vocabulary = json.loads(json_str)
                if not isinstance(vocabulary, list):
                    vocabulary = []
                
                validated_vocabulary = []
                for item in vocabulary:
                    if isinstance(item, dict) and all(k in item for k in ["word", "jiantizi", "pinyin", "english"]):
                        validated_vocabulary.append({
                            "word": item["word"],
                            "jiantizi": item["jiantizi"],
                            "pinyin": item["pinyin"],
                            "english": item["english"]
                        })
                
                logging.info("Vocabulary extraction successful.")
                return validated_vocabulary
            except json.JSONDecodeError as json_err:
                logging.error(f"JSON decoding error: {json_err}")
                return fallback_extraction(cleaned_text)
    except httpx.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {str(http_err)}")
        return fallback_extraction(cleaned_text)
    except Exception as e:
        logging.error(f"Error in extract_vocabulary: {str(e)}")
        return fallback_extraction(cleaned_text)

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
    """Simple fallback method to extract Chinese characters."""
    # Extract unique Chinese characters
    chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Create simple vocabulary items
    return [
        {
            "word": char,
            "jiantizi": char,  # Simplified form (same as original in this fallback)
            "pinyin": "unknown",  # We don't have pinyin in this fallback
            "english": "unknown"  # We don't have translation in this fallback
        }
        for char in list(chinese_chars)[:30]  # Limit to 30 items
    ]