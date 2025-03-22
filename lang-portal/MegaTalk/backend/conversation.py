import time
from typing import Dict, Any, Tuple, Optional
import streamlit as st
from .config import logger, calculate_timeout
from .bedrock_client import call_bedrock_model, call_bedrock_tts, save_audio
from backend.prompts import get_hsk_prompt, get_system_prompt
from pathlib import Path

def call_megaservice(
    user_input: str,
    config_params: Dict[str, Any]
) -> Tuple[str, Optional[bytes], Optional[str], Dict[str, Any]]:
    """Process user input and return response with optional audio"""
    
    request_id = f"frontend_{int(time.time())}_{hash(user_input)}"
    logger.info(f"[{request_id}] Processing request")
    
    details = {
        "timestamp": time.time(),
        "request_id": request_id,
        "input": user_input,
        "config": config_params
    }
    
    text_response = None
    audio_data = None
    error = None
    
    try:
        # Call Bedrock for text response
        text_response = call_bedrock_model(
            prompt=user_input,
            temperature=config_params.get('temperature', 0.7),
            max_tokens=config_params.get('max_tokens', 1000)
        )
        details["text_response"] = text_response
        
        # Generate audio if requested
        if config_params.get('generate_audio'):
            audio_data = call_bedrock_tts(
                text=text_response,
                voice_id=config_params.get('voice', 'default')
            )
            
            if audio_data:
                audio_path = save_audio(audio_data, request_id)
                details["audio_path"] = str(audio_path)
        
    except Exception as e:
        error = str(e)
        logger.error(f"[{request_id}] {error}")
        details["error"] = error
        
    return text_response, audio_data, error, details

def format_prompt(user_input: str, hsk_level: str = "HSK 1 (Beginner)") -> str:
    """Format the prompt for the model with HSK level context"""
    return f"""You are a friendly AI Putonghua buddy.
Please respond in Chinese at {hsk_level} level.
Keep your responses simple and natural.

User: {user_input}
Assistant:"""