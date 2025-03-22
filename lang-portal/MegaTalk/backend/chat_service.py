import json
import time
from typing import Tuple, Optional, Dict, Any
from .config import logger
from .bedrock_client import call_bedrock_model, call_bedrock_tts, save_audio

def get_chat_response(
    prompt: str,
    config_params: Dict[str, Any]
) -> Tuple[Optional[str], Optional[bytes], Optional[str], Dict[str, Any]]:
    """
    Get a chat response and optionally generate audio.
    
    Args:
        prompt: User input text (already formatted with system instructions)
        config_params: Configuration parameters including audio settings
        
    Returns:
        Tuple of (response_text, audio_data, error_message, details)
    """
    try:
        # Get text response from Bedrock
        response_text = call_bedrock_model(prompt)
        if not response_text:
            return None, None, "Failed to get response from language model", {}

        # Generate audio if requested
        audio_data = None
        if config_params.get("generate_audio"):
            try:
                audio_data = call_bedrock_tts(response_text, config_params.get("voice", "default"))
            except Exception as e:
                logger.error(f"TTS generation failed: {str(e)}")
                # Continue even if TTS fails
                
        return response_text, audio_data, None, {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response_text) if response_text else 0,
            "audio_generated": audio_data is not None
        }
        
    except Exception as e:
        error_msg = f"Service error: {str(e)}"
        logger.error(error_msg)
        return None, None, error_msg, {}