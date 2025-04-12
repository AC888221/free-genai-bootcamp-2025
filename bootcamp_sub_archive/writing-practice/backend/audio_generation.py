# audio_generation (added back)

import io
from gtts import gTTS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_audio(text):
    try:
        tts = gTTS(text, lang='zh-CN')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None

# Example usage
if __name__ == "__main__":
    text = "你好，世界！"
    audio = generate_audio(text)
    if audio:
        with open("output.mp3", "wb") as f:
            f.write(audio.getbuffer())