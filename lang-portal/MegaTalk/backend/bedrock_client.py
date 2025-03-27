import boto3
from typing import Optional, Dict, Any
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import (
    logger, 
    BEDROCK_CONFIG, 
    BEDROCK_MODEL_ARN,
    BEDROCK_INFERENCE_CONFIG
)

class BedrockChat:
    def __init__(self, model_id: str = BEDROCK_MODEL_ARN):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            config=BEDROCK_CONFIG
        )
        self.model_id = model_id

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = BEDROCK_INFERENCE_CONFIG  # Use config directly, no transformation needed

        messages = [{
            "role": "user",
            "content": [{"text": message}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return None

# Initialize global client
bedrock_chat = BedrockChat()

def call_bedrock_model(prompt: str) -> Optional[str]:
    """Call Bedrock model with the given prompt."""
    return bedrock_chat.generate_response(prompt)

if __name__ == "__main__":
    # Test the chat functionality
    chat = BedrockChat()
    print("Chat initialized. Type '/exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        response = chat.generate_response(user_input)
        if response:
            print("Bot:", response)
        else:
            print("Error: Failed to get response")