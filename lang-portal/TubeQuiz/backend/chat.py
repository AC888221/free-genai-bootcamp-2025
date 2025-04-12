# Create BedrockChat
# bedrock_chat.py
import boto3
import streamlit as st
from typing import Optional, Dict, Any
import json
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model ID
MODEL_ID = "us.amazon.nova-micro-v1:0"
SYSTEM_MESSAGE = "You are a helpful AI assistant specializing in teaching Putonghua (Standard Mandarin Chinese). You help users learn Chinese grammar, vocabulary, and cultural aspects. Always respond in clear, simple language suitable for language learners."


class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-west-2")
            self.model_id = model_id
            logger.info(f"Successfully initialized Bedrock client with model {model_id} in us-west-2")
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            raise

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        try:
            # Log input parameters
            logger.info(f"Generating response for message length: {len(message)}")
            
            if inference_config is None:
                inference_config = {
                    "temperature": 0.7,
                    "maxTokens": 2048,
                    "stopSequences": [],
                    "topP": 0.9
                }
            logger.debug(f"Using inference config: {json.dumps(inference_config)}")

            # Format messages according to API spec
            messages = [{
                "role": "user",
                "content": [{"text": message}]
            }]

            # Format system message according to API spec
            system = [{"text": SYSTEM_MESSAGE}]

            # Log request details
            logger.debug(f"Request to Bedrock - Model: {self.model_id}")
            logger.debug(f"Messages: {json.dumps(messages)}")
            
            try:
                response = self.bedrock_client.converse(
                    modelId=self.model_id,
                    messages=messages,
                    system=system,
                    inferenceConfig=inference_config
                )
                
                # Log successful response details
                if response.get('usage'):
                    usage_info = f"Tokens used - Input: {response['usage'].get('inputTokens', 0)}, "
                    usage_info += f"Output: {response['usage'].get('outputTokens', 0)}, "
                    usage_info += f"Total: {response['usage'].get('totalTokens', 0)}"
                    logger.info(usage_info)
                    st.info(usage_info)

                if response.get('metrics'):
                    logger.info(f"Latency: {response['metrics'].get('latencyMs', 0)}ms")

                response_text = response['output']['message']['content'][0]['text']
                logger.info(f"Successfully generated response of length: {len(response_text)}")
                return response_text

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                logger.error(f"AWS API Error - Code: {error_code}, Message: {error_msg}")
                if error_code == 'ThrottlingException':
                    st.warning("Rate limit exceeded. Please try again in a few seconds.")
                elif error_code == 'ValidationException':
                    st.error(f"Invalid request: {error_msg}")
                elif error_code == 'ModelTimeoutException':
                    st.warning("Model response timed out. Please try again.")
                else:
                    st.error(f"AWS API Error: {error_msg}")
                return None
                
            except BotoCoreError as e:
                error_msg = f"AWS Connection Error: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
                return None

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            return None


if __name__ == "__main__":
    chat = BedrockChat()
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        response = chat.generate_response(user_input)
        print("Bot:", response)
