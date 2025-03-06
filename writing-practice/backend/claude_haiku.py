# claude_haiku.py (added back)

import json
import logging
from bedrock_client import BedrockClient
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

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
    # Create an instance of BedrockClient
    bedrock_client = BedrockClient(model_id=config.CLAUDE_MODEL_ID)
    client = bedrock_client.get_client()
    
    if client is None:
        logger.error("Failed to create Bedrock client. Please check your AWS configuration.")
        return None
    
    try:
        # Use the generate_response method from BedrockClient
        response = bedrock_client.generate_response(prompt, {"temperature": temperature})
        return response
    
    except Exception as e:
        logger.error(f"Error calling Claude Haiku model: {e}")
        return None