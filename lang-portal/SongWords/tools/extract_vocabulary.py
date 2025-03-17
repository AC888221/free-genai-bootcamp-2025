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

async def extract_vocabulary(text: str) -> List[Dict[str, str]]:
    """Extract vocabulary from text using Bedrock."""
    try:
        logger.info("Starting vocabulary extraction with Bedrock")
        
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
        response_text = response_body.get('completion', '')
        
        # Extract content between JSON tags
        start_idx = response_text.find("[START_JSON]")
        end_idx = response_text.find("[END_JSON]")
        
        if start_idx == -1 or end_idx == -1:
            logger.error("JSON tags not found in response")
            return fallback_extraction(text)
        
        json_str = response_text[start_idx + len("[START_JSON]"):end_idx].strip()
        
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                logger.error("Bedrock response is not a list")
                return fallback_extraction(text)
            
            validated_vocab = []
            for item in data:
                if isinstance(item, dict) and all(k in item for k in ["word", "jiantizi", "pinyin", "english"]):
                    cleaned_item = {
                        "word": str(item["word"]).strip(),
                        "jiantizi": str(item["jiantizi"]).strip(),
                        "pinyin": str(item["pinyin"]).strip(),
                        "english": str(item["english"]).strip()
                    }
                    if contains_chinese(cleaned_item["word"]):
                        validated_vocab.append(cleaned_item)
            
            if not validated_vocab:
                logger.warning("No valid vocabulary items found")
                return fallback_extraction(text)
            
            logger.info(f"Successfully extracted {len(validated_vocab)} vocabulary items")
            return validated_vocab
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return fallback_extraction(text)
            
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