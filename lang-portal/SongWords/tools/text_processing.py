from hanziconv import HanziConv
import logging
import re
from typing import Tuple, List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ['convert_to_simplified', 'clean_chinese_text', 'contains_chinese', 
           'process_chinese_text', 'deduplicate_translations']

def clean_chinese_text(text: str) -> str:
    """
    Clean and normalize Chinese text:
    - Remove URLs
    - Remove markdown formatting
    - Normalize whitespace
    - Remove non-Chinese characters except newlines
    """
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove markdown and other formatting
    text = re.sub(r'\[.*?\]|\(.*?\)|\*\*|__|\*|_|##+', '', text)
    
    # Extract Chinese characters and newlines
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+|\n', text)
    
    # Join with single spaces
    text = ' '.join(chinese_chars)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    logger.info(f"Cleaned text, removed non-Chinese characters. Length: {len(text)}")
    return text.strip()

def contains_chinese(text: str) -> bool:
    """Check if the text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def convert_to_simplified(text: str) -> tuple[str, bool]:
    """
    Convert Traditional Chinese text to Simplified Chinese.
    Returns a tuple of (simplified_text, was_converted)
    """
    simplified_text = HanziConv.toSimplified(text)
    was_converted = simplified_text != text
    if was_converted:
        logger.info("Converted Traditional Chinese characters to Simplified Chinese")
    return simplified_text, was_converted

def process_chinese_text(text: str) -> tuple[str, bool]:
    """
    Process Chinese text:
    1. Clean the text
    2. Convert to Simplified Chinese
    Returns (processed_text, was_converted)
    """
    if not contains_chinese(text):
        logger.warning("No Chinese characters found in text")
        return text, False
        
    cleaned_text = clean_chinese_text(text)
    simplified_text, was_converted = convert_to_simplified(cleaned_text)
    
    return simplified_text, was_converted 

def deduplicate_translations(translations: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate translations while preserving order.
    
    Args:
        translations (List[Dict[str, str]]): List of translation dictionaries
        
    Returns:
        List[Dict[str, str]]: Deduplicated translations
    """
    seen = set()
    unique_translations = []
    for t in translations:
        # Create a tuple of the values to use as a hash key
        key = (t['original'], t['pinyin'], t['english'])
        if key not in seen:
            seen.add(key)
            unique_translations.append(t)
    
    logger.info(f"Deduplicated translations from {len(translations)} to {len(unique_translations)} items")
    return unique_translations 