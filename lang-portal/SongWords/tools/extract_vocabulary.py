import re
import json
import os
import boto3
from botocore.config import Config
from typing import List, Dict, Any
import logging

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

async def extract_vocabulary(text: str) -> List[Dict[str, Any]]:
    """Extract vocabulary from text using Bedrock."""
    try:
        logger.info("Starting vocabulary extraction with Bedrock")
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        prompt = """Human: Extract Chinese vocabulary from this text. 
        Include common words and phrases.
        
        Text: {text}
        
        Return in JSON format:
        [
            {{"word": "你好", "pinyin": "nǐ hǎo", "english": "hello"}},
            {{"word": "再见", "pinyin": "zài jiàn", "english": "goodbye"}}
        ]

        Assistant: Here's the vocabulary in JSON format:"""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.format(text=text)
                }
            ]
        })
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        vocabulary_text = response_body.get('content', [])[0].get('text', '').strip()
        
        # Extract JSON from response text
        import re
        json_match = re.search(r'\[.*\]', vocabulary_text, re.DOTALL)
        if json_match:
            vocabulary = json.loads(json_match.group(0))
        else:
            vocabulary = []
            
        return vocabulary
    except Exception as e:
        logger.error(f"Error in extract_vocabulary: {str(e)}")
        return fallback_extraction(text)

def clean_chinese_text(text: str) -> str:
    """Clean the text to focus on Chinese content."""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\[.*?\]|\(.*?\)|\*\*|__|\*|_|##+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def contains_chinese(text: str) -> bool:
    """Check if the text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def fallback_extraction(text: str) -> List[Dict[str, Any]]:
    """Simple fallback method to extract Chinese characters."""
    chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
    return [
        {
            "word": char,
            "jiantizi": char,
            "pinyin": "unknown",
            "english": "unknown"
        }
        for char in list(chinese_chars)[:30]
    ]