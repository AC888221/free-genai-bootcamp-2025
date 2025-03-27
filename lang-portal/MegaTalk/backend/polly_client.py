import boto3
from time import sleep
from typing import Optional
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import logger, POLLY_CONFIG, POLLY_DEFAULTS

# Use existing audio directory
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio")

class PollyTTS:
    def __init__(self):
        """Initialize Amazon Polly client"""
        self.polly_client = boto3.client('polly', config=POLLY_CONFIG)

    def generate_audio(
        self,
        text: str,
        voice_id: str = POLLY_DEFAULTS["voice_id"],
        pitch: str = POLLY_DEFAULTS["pitch"],
        rate: str = POLLY_DEFAULTS["rate"],
        volume: str = POLLY_DEFAULTS["volume"],
        retries: int = 3
    ) -> Optional[bytes]:
        """Generate audio using Amazon Polly with SSML support"""
        ssml_text = f'<speak><prosody pitch="{pitch}" rate="{rate}" volume="{volume}">{text}</prosody></speak>'
        
        for attempt in range(retries):
            try:
                response = self.polly_client.synthesize_speech(
                    Text=ssml_text,
                    VoiceId=voice_id,
                    OutputFormat='mp3',
                    TextType='ssml'
                )
                return response['AudioStream'].read()
            except boto3.exceptions.Boto3Error as e:
                logger.error(f"Error generating audio (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None

# Initialize global client
polly_tts = PollyTTS()

def call_polly_tts(
    text: str,
    voice_id: str = POLLY_DEFAULTS["voice_id"],
    pitch: str = POLLY_DEFAULTS["pitch"],
    rate: str = POLLY_DEFAULTS["rate"],
    volume: str = POLLY_DEFAULTS["volume"]
) -> Optional[bytes]:
    """Call Polly TTS service with the given text."""
    return polly_tts.generate_audio(text, voice_id, pitch, rate, volume)

if __name__ == "__main__":
    # Test the TTS functionality
    test_text = "你好，我是你的语言助手。"
    audio_data = call_polly_tts(test_text)
    if audio_data:
        output_path = os.path.join(AUDIO_DIR, "test_audio.mp3")
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"Audio file generated: {output_path}")
    else:
        print("Failed to generate audio")
