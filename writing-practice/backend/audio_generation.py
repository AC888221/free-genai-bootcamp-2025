# audio_generation (added back)

import io
from gtts import gTTS
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.experimental_memo(ttl=300)
def generate_audio(text):
    try:
        tts = gTTS(text, lang='zh-CN')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        st.error("Failed to generate audio. Please try again.")
        return None