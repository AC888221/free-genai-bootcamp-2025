import pytest
import boto3
import json
import os
import logging
from botocore.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBedrockIntegration:
    @pytest.fixture(scope="class")
    def bedrock_client(self):
        config = Config(
            region_name=os.getenv("AWS_REGION", "us-west-2"),
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        return boto3.client('bedrock-runtime', config=config)

    def test_llm_connection(self, bedrock_client):
        """Test basic connection to Bedrock LLM"""
        try:
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": ["text", "Test connection"]}
                ]
            })
            
            response = bedrock_client.invoke_model(
                modelId="arn:aws:bedrock:us-west-2:116981786576:inference-profile/us.amazon.nova-micro-v1:0",
                body=body
            )
            
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            logger.info("✅ LLM connection test passed")
        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {str(e)}")
            raise

    def test_chinese_response(self, bedrock_client):
        """Test Chinese language generation"""
        try:
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": ["text", "Please respond in Chinese: How are you?"]}
                ]
            })
            
            response = bedrock_client.invoke_model(
                modelId="arn:aws:bedrock:us-west-2:116981786576:inference-profile/us.amazon.nova-micro-v1:0",
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['messages'][-1]['content'][1] if 'messages' in response_body else response_body.get('outputText', '')
            assert any('\u4e00' <= char <= '\u9fff' for char in response_text)
            logger.info("✅ Chinese response test passed")
            logger.info(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Chinese response test failed: {str(e)}")
            raise

    def test_hsk1_level(self, bedrock_client):
        """Test HSK1 level response"""
        try:
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": ["text", """I want you to be a friendly AI Putonghua buddy.
                    Use only HSK1 vocabulary (150 basic words).
                    Keep sentences under 5 words.
                    What's your name?"""]}
                ]
            })
            
            response = bedrock_client.invoke_model(
                modelId="arn:aws:bedrock:us-west-2:116981786576:inference-profile/us.amazon.nova-micro-v1:0",
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['messages'][-1]['content'][1] if 'messages' in response_body else response_body.get('outputText', '')
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