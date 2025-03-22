import json
import boto3
import time
from pathlib import Path
from typing import Optional
from .config import BEDROCK_CONFIG, logger, AUDIO_DIR

# Initialize Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        config=BEDROCK_CONFIG
    )
    logger.info("Successfully initialized Bedrock client")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {str(e)}")
    bedrock_runtime = None

def call_bedrock_model(prompt: str) -> str:
    """Call AWS Bedrock model for text generation."""
    try:
        # Format the request according to Nova's requirements
        body = json.dumps({
            "messages": [
                {"role": "user", "content": ["text", prompt]}
            ]
        })
        
        logger.info(f"Sending request to Bedrock: {body}")
        
        response = bedrock_runtime.invoke_model(
            modelId="arn:aws:bedrock:us-west-2:116981786576:inference-profile/us.amazon.nova-micro-v1:0",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        logger.info(f"Received response: {response_body}")
        
        # Extract the assistant's message from the response
        if 'messages' in response_body and len(response_body['messages']) > 0:
            return response_body['messages'][-1]['content']
        elif 'content' in response_body:
            return response_body['content']
        else:
            return response_body.get('outputText', '')
        
    except Exception as e:
        logger.error(f"Bedrock API error: {str(e)}")
        raise

def call_bedrock_tts(text: str, voice_id: str = "amazon.neural-text-to-speech") -> bytes:
    """Call AWS Bedrock for text-to-speech."""
    try:
        body = json.dumps({
            "text": text,
            "voice_id": voice_id,
            "engine": "neural"
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=voice_id,
            body=body
        )
        
        return response.get('body').read()
    except Exception as e:
        logger.error(f"Bedrock TTS API error: {str(e)}")
        raise

def save_audio(audio_data: bytes, request_id: str) -> Path:
    """Save audio data to file and return the path."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"response_{timestamp}_{request_id[:8]}.wav"
    audio_path = AUDIO_DIR / filename
    
    with open(audio_path, "wb") as f:
        f.write(audio_data)
    
    return audio_path