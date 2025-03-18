# bedrock_client.py

import boto3
import json
import logging
from typing import Optional, Dict, Any
import sys
import os
import traceback

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, model_id: str = None):
        """Initialize Bedrock client"""
        try:
            # Use the provided model_id or fall back to the one in config
            self.model_id = model_id if model_id else config.CLAUDE_MODEL_ID
            logger.info(f"Attempting to create Bedrock client for model: {self.model_id}")
            
            # Create a session with explicit credentials
            session = boto3.Session(
                region_name=config.BEDROCK_REGION
            )
            
            # Print session details for debugging
            credentials = session.get_credentials()
            if credentials:
                logger.info(f"Using AWS credentials with access key ID: {credentials.access_key[:4]}...")
                logger.info(f"Using region: {session.region_name}")
            
            # Create the bedrock-runtime client
            self.client = session.client('bedrock-runtime')
            logger.info(f"Successfully created Bedrock client in region {config.BEDROCK_REGION}.")
            
            # Try to list available models for diagnostic purposes
            try:
                bedrock_client = session.client('bedrock')
                response = bedrock_client.list_foundation_models()
                available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
                logger.info(f"Available models: {available_models}")
                
                if self.model_id not in available_models:
                    logger.warning(f"Model {self.model_id} is not in the list of available models. You may need to request access.")
                    # Try to find Claude models that are available
                    claude_models = [model for model in available_models if 'claude' in model.lower()]
                    if claude_models:
                        logger.info(f"Available Claude models: {claude_models}")
                        # Suggest using one of these models instead
                        logger.info(f"Consider using one of these models instead by updating config.py")
            except Exception as e:
                logger.warning(f"Could not list available models: {str(e)}")
                
        except boto3.exceptions.Boto3Error as e:
            logger.error(f"Boto3 error creating Bedrock client: {e}")
            logger.error(traceback.format_exc())
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error creating Bedrock client: {e}")
            logger.error(traceback.format_exc())
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
            
            logger.info(f"Invoking model {self.model_id} in region {config.BEDROCK_REGION}")
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('content')[0].get('text')
            
        except boto3.exceptions.Boto3Error as e:
            if "AccessDeniedException" in str(e):
                logger.error(f"Access denied to model {self.model_id}: {str(e)}")
                logger.error("Please ensure you have requested access to this model in the AWS Bedrock console.")
                logger.error(f"Current region: {config.BEDROCK_REGION}")
                logger.error("To request access: Go to AWS Bedrock console > Model access > Request access")
                logger.error("After requesting access, it may take some time for the access to be granted.")
            else:
                logger.error(f"Boto3 error generating response: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating response: {str(e)}")
            logger.error(traceback.format_exc())
            return None

if __name__ == "__main__":
    # Example usage and diagnostic tool
    print("Running Bedrock client diagnostic...")
    
    # List available regions for Bedrock
    try:
        session = boto3.Session()
        regions = session.get_available_regions('bedrock-runtime')
        print(f"Available regions for bedrock-runtime: {regions}")
        
        # Check if the configured region is in the list
        if config.BEDROCK_REGION not in regions:
            print(f"WARNING: Configured region {config.BEDROCK_REGION} is not in the list of available regions!")
            print(f"Consider changing to one of these regions in config.py: {regions}")
    except Exception as e:
        print(f"Error listing regions: {str(e)}")
    
    # Print the model ID from config
    print(f"Model ID from config: {config.CLAUDE_MODEL_ID}")
    
    # Test the client
    client = BedrockClient()
    if client.get_client() is not None:
        print(f"Testing connection to model {client.model_id} in region {config.BEDROCK_REGION}")
        try:
            response = client.generate_response("Hello, how are you?")
            if response:
                print("Response from Bedrock:", response)
            else:
                print("Failed to get a response from Bedrock.")
                print("Please check the following:")
                print("1. You have requested access to the model in the AWS Bedrock console")
                print("2. The model is available in your region")
                print("3. Your AWS credentials have the correct permissions")
                print(f"4. The model ID is correct: {client.model_id}")
        except Exception as e:
            print(f"Error testing Bedrock client: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("Failed to initialize Bedrock client.")