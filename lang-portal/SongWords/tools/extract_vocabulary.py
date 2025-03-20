import re
import json
import os
import boto3
from botocore.config import Config
from typing import List, Dict, Any, Tuple
import logging
from .text_processing import process_chinese_text

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

async def extract_vocabulary(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extract vocabulary from text using Bedrock.
    Returns a tuple of (simplified_text, vocabulary_list)
    """
    try:
        logger.info("Starting vocabulary extraction with Bedrock")
        
        # Process the text (clean and convert to Simplified Chinese)
        simplified_text, was_converted = process_chinese_text(text)
        if not simplified_text:
            logger.warning("No valid Chinese text found to process")
            return text, []
        
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        prompt = """Human: Extract Simplified Chinese (Putonghua) vocabulary from this text. 
        Include meaningful words and phrases, not just individual characters unless they stand alone as words.
        If any Traditional Chinese characters are found, convert them to their Simplified Chinese equivalents.
        
        Text: {text}
        
        Return ONLY in this exact JSON format:
        [
            {{"jiantizi": "你好", "pinyin": "nǐ hǎo", "english": "hello"}},
            {{"jiantizi": "再见", "pinyin": "zài jiàn", "english": "goodbye"}}
        ]
        
        Note: 
        1. Ensure all Chinese characters are in Simplified Chinese (jiantizi) form
        2. Group characters into meaningful words, not individual characters
        3. Return ONLY the JSON array, no additional text

        Assistant:"""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.format(text=simplified_text)
                }
            ]
        })
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        vocabulary_text = response_body.get('content', [])[0].get('text', '').strip()
        
        # Extract JSON from response text - more robust pattern to find JSON
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', vocabulary_text, re.DOTALL)
        if json_match:
            try:
                vocabulary = json.loads(json_match.group(0))
                logger.info(f"Successfully extracted {len(vocabulary)} vocabulary items")
                
                # Validate the structure of each item
                valid_vocabulary = []
                for item in vocabulary:
                    if all(key in item for key in ["jiantizi", "pinyin", "english"]):
                        valid_vocabulary.append(item)
                    else:
                        logger.warning(f"Invalid vocabulary item format: {item}")
                
                return simplified_text, valid_vocabulary
            except json.JSONDecodeError:
                logger.error(f"Could not parse JSON: {vocabulary_text}")
                return simplified_text, []
        else:
            logger.warning("Could not find JSON in response")
            return simplified_text, []
            
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