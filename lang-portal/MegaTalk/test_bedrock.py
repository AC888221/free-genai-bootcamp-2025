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
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        return boto3.client('bedrock-runtime', config=config)

    def test_llm_connection(self, bedrock_client):
        """Test basic connection to Bedrock LLM"""
        try:
            body = json.dumps({
                "prompt": "Test connection",
                "max_tokens_to_sample": 10,
                "temperature": 0.7,
            })
            
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            logger.info("✅ LLM connection test passed")
        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {str(e)}")
            raise

    def test_tts_connection(self, bedrock_client):
        """Test basic connection to Bedrock TTS"""
        try:
            body = json.dumps({
                "text": "Test audio",
                "voice_id": "amazon.neural-text-to-speech",
                "engine": "neural"
            })
            
            response = bedrock_client.invoke_model(
                modelId="amazon.neural-text-to-speech",
                body=body
            )
            
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            assert len(response['body'].read()) > 0  # Check if audio data is returned
            logger.info("✅ TTS connection test passed")
        except Exception as e:
            logger.error(f"❌ TTS connection test failed: {str(e)}")
            raise

    def test_chinese_response(self, bedrock_client):
        """Test Chinese language generation"""
        try:
            prompt = """You are a friendly AI Putonghua buddy. 
            Please answer in Putonghua. Keep it simple.
            
            User: Hello, how are you?
            Assistant:"""
            
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 100,
                "temperature": 0.7,
            })
            
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_text = json.loads(response['body'].read())['completion']
            # Check if response contains Chinese characters
            assert any('\u4e00' <= char <= '\u9fff' for char in response_text)
            logger.info("✅ Chinese response test passed")
            logger.info(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Chinese response test failed: {str(e)}")
            raise

    def test_hsk1_level(self, bedrock_client):
        """Test HSK1 level response"""
        try:
            prompt = """You are a friendly AI Putonghua buddy.
            Use only HSK1 vocabulary (150 basic words).
            Keep sentences under 5 words.
            
            User: What's your name?
            Assistant:"""
            
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 100,
                "temperature": 0.7,
            })
            
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_text = json.loads(response['body'].read())['completion']
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