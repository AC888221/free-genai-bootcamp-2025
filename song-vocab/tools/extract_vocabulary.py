import re
import json
from typing import List, Dict, Any
import ollama

def extract_vocabulary(text: str) -> List[Dict[str, Any]]:
    """
    Extract vocabulary from Chinese (Putonghua) text.
    
    Args:
        text (str): The text to extract vocabulary from
        
    Returns:
        List[Dict[str, Any]]: A list of vocabulary items with word, jiantizi, pinyin, and English translation
    """
    # Use the LLM to extract vocabulary
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
    
    # Clean the text to focus on Chinese content
    cleaned_text = clean_chinese_text(text)
    
    if not contains_chinese(cleaned_text):
        return []
    
    try:
        # Call Ollama to process the text
        response = ollama.chat(
            model="phi4-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract vocabulary from the following text:\n\n{cleaned_text[:5000]}"}
            ]
        )
        
        # Extract JSON from the response
        response_content = response["message"]["content"]
        
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Look for arrays in the text if no JSON code block
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback to the entire response
                json_str = response_content
        
        try:
            # Parse the JSON
            vocabulary = json.loads(json_str)
            
            # Ensure it's a list
            if not isinstance(vocabulary, list):
                vocabulary = []
            
            # Validate each item
            validated_vocabulary = []
            for item in vocabulary:
                if isinstance(item, dict) and all(k in item for k in ["word", "jiantizi", "pinyin", "english"]):
                    validated_vocabulary.append({
                        "word": item["word"],
                        "jiantizi": item["jiantizi"],
                        "pinyin": item["pinyin"],
                        "english": item["english"]
                    })
            
            return validated_vocabulary
        except json.JSONDecodeError:
            # If JSON parsing fails, try a simpler approach
            return fallback_extraction(cleaned_text)
    except Exception as e:
        print(f"Error in extract_vocabulary: {str(e)}")
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