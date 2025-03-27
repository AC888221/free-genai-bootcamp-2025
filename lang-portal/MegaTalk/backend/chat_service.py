import json
import time
import sys
import os
from typing import Tuple, Optional, Dict, Any

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import logger
from backend.bedrock_client import call_bedrock_model
from backend.polly_client import call_polly_tts

def get_chat_response(
    prompt: str,
    config_params: Dict[str, Any]
) -> Tuple[str, Optional[bytes], Optional[str], dict]:
    """Get response from the language model."""
    try:
        # Get text response from Bedrock
        response_text = call_bedrock_model(prompt)
        if not response_text:
            logger.error("No response text received from Bedrock")
            return "", None, "Failed to get response from language model", {}

        # Generate audio if requested
        audio_data = None
        if config_params.get("generate_audio"):
            try:
                # Let's log what we're receiving
                logger.info(f"Voice config received: {config_params.get('voice', 'Zhiyu')}")
                audio_data = call_polly_tts(
                    response_text,
                    voice_id=config_params.get("voice", "Zhiyu")  # Check if this matches what polly_client expects
                )
                if not audio_data:
                    logger.error("No audio data received from Polly")
            except Exception as e:
                logger.error(f"TTS generation failed: {str(e)}")
                # Continue even if TTS fails
                
        response_details = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response_text) if response_text else 0,
            "audio_generated": audio_data is not None
        }
        logger.info(f"Response Details: {response_details}")
        
        return response_text, audio_data, None, response_details
        
    except Exception as e:
        logger.error(f"Service error: {str(e)}")
        return "", None, f"Service error: {str(e)}", {}