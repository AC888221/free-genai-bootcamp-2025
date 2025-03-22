import pytest
import boto3
import json
import os
import logging
from backend.config import (
    logger,
    BEDROCK_CONFIG,
    BEDROCK_MODEL_ARN,
    BEDROCK_INFERENCE_CONFIG
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBedrockIntegration:
    @pytest.fixture
    def bedrock_client(self):
        return boto3.client('bedrock-runtime', config=BEDROCK_CONFIG)

    def test_llm_connection(self, bedrock_client):
        """Test basic connection to Bedrock LLM"""
        try:
            messages = [{
                "role": "user",
                "content": [{"text": "Test connection"}]
            }]
            
            response = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ARN,
                messages=messages,
                inferenceConfig=BEDROCK_INFERENCE_CONFIG
            )
            
            assert response['output']['message']['content'][0]['text']
            logger.info("✅ LLM connection test passed")
        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {str(e)}")
            raise

    def test_chinese_response(self, bedrock_client):
        """Test Chinese language generation"""
        try:
            messages = [{
                "role": "user",
                "content": [{"text": "Please respond in Chinese: How are you?"}]
            }]
            
            response = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ARN,
                messages=messages,
                inferenceConfig=BEDROCK_INFERENCE_CONFIG
            )
            
            response_text = response['output']['message']['content'][0]['text']
            assert response_text
            logger.info("✅ Chinese response test passed")
            logger.info(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Chinese response test failed: {str(e)}")
            raise

    def test_hsk1_level(self, bedrock_client):
        """Test HSK1 level response"""
        try:
            messages = [{
                "role": "user",
                "content": [{"text": """I want you to be a friendly AI Putonghua buddy.
                Use only HSK1 vocabulary (150 basic words).
                Keep sentences under 5 words.
                What's your name?"""}]
            }]
            
            response = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ARN,
                messages=messages,
                inferenceConfig=BEDROCK_INFERENCE_CONFIG
            )
            
            response_text = response['output']['message']['content'][0]['text']
            assert response_text
            logger.info("✅ HSK1 response test passed")
            logger.info(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ HSK1 response test failed: {str(e)}")
            raise

def main():
    """Run all tests and display results"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    main() 