# claude_haiku.py (added back)

import json
import logging
from bedrock_client import get_bedrock_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_claude_haiku(prompt, temperature=0.7, max_tokens=1000):
    client = get_bedrock_client()
    
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