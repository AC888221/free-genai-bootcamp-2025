# claude_haiku.py (added back)

import json
import logging
from bedrock_client import get_bedrock_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_claude_haiku(prompt, temperature=0.7, max_tokens=1000):
    """
    Call the Claude Haiku model to generate a haiku based on the provided prompt.
    
    Args:
        prompt (str): The prompt to generate the haiku.
        temperature (float): The temperature setting for the model.
        max_tokens (int): The maximum number of tokens to generate.
    
    Returns:
        str: The generated haiku text, or None if an error occurs.
    """
    client = get_bedrock_client()
    if client is None:
        logger.error("Failed to create Bedrock client. Please check your AWS configuration.")
        return None
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",  # Claude 3 Haiku model ID
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('content')[0].get('text')
    
    except Exception as e:
        logger.error(f"Error calling Claude Haiku model: {e}")
        return None