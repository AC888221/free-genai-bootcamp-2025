# bedrock_client.py (added back)

import boto3
import json
import logging
from typing import Optional, Dict, Any
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, model_id: str = config.CLAUDE_MODEL_ID):
        """Initialize Bedrock client"""
        try:
            logger.info("Attempting to create Bedrock client...")
            self.client = boto3.client('bedrock-runtime', region_name=config.BEDROCK_REGION)
            self.model_id = model_id
            logger.info("Successfully created Bedrock client.")
        except boto3.exceptions.Boto3Error as e:
            logger.error(f"Boto3 error creating Bedrock client: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error creating Bedrock client: {e}")
            self.client = None

    def get_client(self):
        return self.client

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if self.client is None:
            logger.error("Bedrock client is not initialized")
            return None
            
        if inference_config is None:
            inference_config = {"temperature": 0.7}
            
        try:
            # For Claude models, use the invoke_model method with the appropriate request format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": inference_config.get("temperature", 0.7),
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('content')[0].get('text')
            
        except boto3.exceptions.Boto3Error as e:
            logger.error(f"Boto3 error generating response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating response: {str(e)}")
            return None

if __name__ == "__main__":
    # Example usage
    client = BedrockClient()
    response = client.generate_response("Hello, how are you?")
    if response:
        print("Response from Bedrock:", response)
    else:
        print("Failed to get a response from Bedrock.")