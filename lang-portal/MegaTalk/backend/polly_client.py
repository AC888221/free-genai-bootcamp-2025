import boto3
from time import sleep
from typing import Optional
import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import logger, POLLY_CONFIG, POLLY_DEFAULTS

# Use existing audio directory
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio")

class PollyTTS:
    def __init__(self):
        """Initialize Amazon Polly client"""
        try:
            self.polly_client = boto3.client('polly', config=POLLY_CONFIG)
            self.sessions_dir = os.path.join(AUDIO_DIR, "sessions")
            os.makedirs(self.sessions_dir, exist_ok=True)
            logger.info("Successfully initialized Polly TTS client")
        except Exception as e:
            logger.error(f"Failed to initialize Polly client: {str(e)}")
            raise

    def generate_audio(
        self,
        text: str,
        session_id: str,
        message_id: str,
        voice_id: str = POLLY_DEFAULTS["voice_id"],
        pitch: str = POLLY_DEFAULTS["pitch"],
        rate: str = POLLY_DEFAULTS["rate"],
        volume: str = POLLY_DEFAULTS["volume"],
        retries: int = 3
    ) -> Optional[tuple[bytes, str]]:
        """Generate audio using Amazon Polly with SSML support and save to file"""
        logger.info(f"Generating audio for text of length {len(text)}")
        ssml_text = f'<speak><prosody pitch="{pitch}" rate="{rate}" volume="{volume}">{text}</prosody></speak>'
        
        for attempt in range(retries):
            try:
                response = self.polly_client.synthesize_speech(
                    Text=ssml_text,
                    VoiceId=voice_id,
                    OutputFormat='mp3',
                    TextType='ssml'
                )
                audio_data = response['AudioStream'].read()
                
                session_dir = os.path.join(self.sessions_dir, session_id)
                os.makedirs(session_dir, exist_ok=True)
                
                filename = f"{message_id}.mp3"
                filepath = os.path.join(session_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(audio_data)
                logger.info(f"Audio saved to: {filepath}")
                
                return audio_data, filepath
                
            except Exception as e:
                logger.error(f"Error generating audio (attempt {attempt + 1}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None, None

# Initialize global client
polly_tts = PollyTTS()

def call_polly_tts(
    text: str,
    session_id: str,
    message_id: str,
    voice_id: str = POLLY_DEFAULTS["voice_id"],
    pitch: str = POLLY_DEFAULTS["pitch"],
    rate: str = POLLY_DEFAULTS["rate"],
    volume: str = POLLY_DEFAULTS["volume"]
) -> Optional[tuple[bytes, str]]:
    """Call Polly TTS service with the given text and save to session directory."""
    return polly_tts.generate_audio(
        text, 
        session_id, 
        message_id, 
        voice_id, 
        pitch, 
        rate, 
        volume
    )

if __name__ == "__main__":
    # Test the TTS functionality
    test_text = "你好，我是你的语言助手。"
    test_session_id = "test_session"
    test_message_id = "test_message"
    audio_data, filepath = call_polly_tts(test_text, test_session_id, test_message_id)
    if audio_data:
        print(f"Audio file generated: {filepath}")
    else:
        print("Failed to generate audio")
