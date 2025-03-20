import re
import json
import os
import boto3
from botocore.config import Config
from typing import List, Dict, Any, Tuple
import logging
from .text_processing import (process_chinese_text, convert_to_simplified, 
                            contains_chinese, deduplicate_translations)
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for Claude 3 Sonnet interaction
MAX_CHARS_PER_CHUNK = 2000  # Conservative estimate for input text

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    config=Config(
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
)

async def extract_lyrics_and_segment(text: str) -> List[str]:
    """
    Extract lyrics from text and segment them into verses/stanzas.
    
    Args:
        text (str): The text to process
        
    Returns:
        List[str]: List of verses in Simplified Chinese
    """
    prompt = """Extract and segment the Chinese lyrics into natural verses or stanzas.
    Return only the segmented lyrics, one verse per line, with no additional formatting.
    Focus on meaningful verse breaks that follow the song's structure.
    
    Text: {text}
    
    For example:
    月亮代表我的心 你问我爱你有多深
    我爱你有几分 我的情也真 我的爱也真
    月亮代表我的心
    """
    
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.format(text=text)
                }
            ]
        })
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        segments = response_body.get('content', [])[0].get('text', '').strip().split('\n')
        segments = [s.strip() for s in segments if s.strip()]
        
        # Double-check that all segments are in Simplified Chinese
        simplified_segments = []
        for segment in segments:
            simplified_text, was_converted = convert_to_simplified(segment)
            if contains_chinese(simplified_text):  # Only include segments with Chinese characters
                simplified_segments.append(simplified_text)
        
        return list(dict.fromkeys(simplified_segments))  # Remove duplicates while preserving order
        
    except Exception as e:
        logger.error(f"Error extracting lyrics segments: {str(e)}")
        return []

async def translate_segment(segment: str) -> List[Dict[str, str]]:
    """
    Translate a verse into vocabulary units with Pinyin and English.
    
    Args:
        segment (str): The verse to translate (in Simplified Chinese)
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing translations for each vocabulary unit
    """
    prompt = """Break down this Chinese verse into the smallest vocabulary units without altering the meaning of the verse and translate each unit.
    Focus on meaningful units like:
    - Individual words (词语)
    - Compound words (复合词)
    - Common phrases (短语)
    - Measure words (量词)
    - Important grammatical particles (语气词)
    
    Text: {text}
    
    Example input:
    Text: 你问我爱你有多深
    
    Return each vocabulary unit in this format:
    Word(s):
    Pinyin: [pinyin with tones]
    English: [concise translation]
    
    Example output:
    Word(s): 月亮
    Pinyin: yuè liàng
    English: moon
    
    Word(s): 代表
    Pinyin: dài biǎo
    English: represent, symbolize
    
    Word(s): 我的
    Pinyin: wǒ de
    English: my, mine
    
    Word(s): 心
    Pinyin: xīn
    English: heart
    """
    
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.format(text=segment)
                }
            ]
        })
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        translation_text = response_body.get('content', [])[0].get('text', '').strip()
        
        # Parse the response into individual vocabulary units
        translations = []
        current_unit = {}
        
        for line in translation_text.split('\n'):
            if line.strip():
                if line.startswith('Word(s):'):
                    if current_unit:
                        translations.append(current_unit)
                    current_unit = {'original': line.split(':', 1)[1].strip()}
                elif line.startswith('Pinyin:'):
                    current_unit['pinyin'] = line.split(':', 1)[1].strip()
                elif line.startswith('English:'):
                    current_unit['english'] = line.split(':', 1)[1].strip()
        
        # Add the last unit
        if current_unit:
            translations.append(current_unit)
        
        # Validate that each translation has all required fields
        validated_translations = []
        for trans in translations:
            if all(key in trans for key in ['original', 'pinyin', 'english']):
                validated_translations.append(trans)
        
        return validated_translations
        
    except Exception as e:
        logger.error(f"Error translating vocabulary unit: {str(e)}")
        return []

async def extract_vocabulary(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Process Chinese lyrics: extract, segment, and translate.
    
    Args:
        text (str): The Chinese text to process
        
    Returns:
        Tuple[str, List[Dict[str, Any]]]: (simplified_text, translations)
    """
    try:
        logger.info("Starting lyrics processing")
        
        # First, process the input text
        simplified_text, was_converted = process_chinese_text(text)
        if not simplified_text:
            logger.warning("No valid Chinese text found to process")
            return text, []
        
        # Extract and segment lyrics (text is already simplified)
        segments = await extract_lyrics_and_segment(simplified_text)
        logger.info(f"Extracted {len(segments)} segments")
        
        # Process segments with increased delay between calls
        translations = []
        for i, segment in enumerate(segments):
            # Add longer delay between segments to avoid rate limits
            if i > 0:
                await asyncio.sleep(3)
            
            translation = await translate_segment(segment)
            if translation:
                translations.extend(translation)
            logger.info(f"Translated segment {i+1}/{len(segments)}")
        
        # Deduplicate translations
        unique_translations = deduplicate_translations(translations)
        
        return simplified_text, unique_translations
            
    except Exception as e:
        logger.error(f"Error in extract_vocabulary: {str(e)}")
        return text, []

def clean_chinese_text(text: str) -> str:
    """Clean the text to focus on Simplified Chinese content."""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\[.*?\]|\(.*?\)|\*\*|__|\*|_|##+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def contains_chinese(text: str) -> bool:
    """Check if the text contains Simplified Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def fallback_extraction(text: str) -> List[Dict[str, Any]]:
    """Simple fallback method to extract Simplified Chinese characters."""
    chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
    return [
        {
            "jiantizi": char,
            "pinyin": "unknown",
            "english": "unknown"
        }
        for char in list(chinese_chars)[:30]
    ]