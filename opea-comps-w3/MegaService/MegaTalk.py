import streamlit as st
import requests
import base64
import io
from typing import Optional
import os
import logging
import sys
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/megatalk.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
MEGASERVICE_URL = os.getenv("MEGASERVICE_URL", "http://localhost:9500")

st.set_page_config(
    page_title="OPEA MegaTalk",
    page_icon="🤖",
    layout="wide",
)

# Title and description
st.title("🤖 OPEA MegaTalk")
st.markdown("### Conversational AI with Voice Response")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    model = st.selectbox(
        "LLM Model",
        ["Qwen/Qwen2.5-0.5B-Instruct", "other-model-1", "other-model-2"],
        index=0
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100,
        help="Maximum number of tokens to generate"
    )
    
    voice = st.selectbox(
        "Voice",
        ["default", "voice1", "voice2"],
        index=0
    )
    
    generate_audio = st.checkbox("Generate Audio", value=True)

# Main content area
user_input = st.text_area("Enter your message:", height=150)

# Add startup logging
logger.info("Starting MegaTalk application")
logger.info(f"MEGASERVICE_URL: {MEGASERVICE_URL}")

def call_megaservice(text: str, generate_audio: bool = True) -> tuple[Optional[str], Optional[bytes], Optional[str]]:
    """
    Call the megaservice with error handling and retries.
    Returns: (text_response, audio_data, error_message)
    """
    try:
        with st.spinner("Processing request..."):
            response = requests.post(
                f"{MEGASERVICE_URL}/v1/megaservice",
                json={
                    "text": text,
                    "generate_audio": generate_audio,
                    "model": "Qwen/Qwen2.5-0.5B-Instruct",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=60
            )
            
            if response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(response.content))
                except:
                    error_detail = str(response.content)
                return None, None, f"Service error ({response.status_code}): {error_detail}"
            
            data = response.json()
            text_response = data.get("text_response")
            
            # Handle audio data and potential errors
            audio_data = None
            if generate_audio:
                if data.get("audio_data"):
                    try:
                        audio_bytes = base64.b64decode(data["audio_data"])
                        audio_data = audio_bytes
                    except Exception as e:
                        st.warning(f"Audio decoding failed: {str(e)}")
                elif data.get("error_message"):
                    st.warning(f"Audio generation issue: {data['error_message']}")
            
            return text_response, audio_data, None
            
    except requests.exceptions.Timeout:
        return None, None, "Request timed out. The service might be busy trying different endpoints."
    except requests.exceptions.ConnectionError:
        return None, None, "Could not connect to the service. Please check if it's running."
    except Exception as e:
        return None, None, f"Error: {str(e)}"

if st.button("Submit"):
    if not user_input.strip():
        st.error("Please enter a message")
        logger.warning("Empty input submitted")
    else:
        with st.spinner("Processing..."):
            try:
                logger.info(f"Sending request to megaservice: {user_input[:100]}...")
                text_response, audio_data, error = call_megaservice(user_input, generate_audio)
                
                if error:
                    st.error(error)
                else:
                    logger.info("Successfully received response from megaservice")
                    
                    # Display text response
                    st.subheader("Text Response")
                    st.write(text_response)
                    
                    # Display audio if available
                    if generate_audio and audio_data:
                        st.subheader("Audio Response")
                        st.audio(audio_data, format="audio/wav")
                        
                        # Add download button for audio
                        st.download_button(
                            label="Download Audio",
                            data=audio_data,
                            file_name=f"response.wav",
                            mime="audio/wav"
                        )
                    
                    # Add to chat history
                    if "chat_history" not in st.session_state:
                        st.session_state.chat_history = []
                    st.session_state.chat_history.append((user_input, text_response, audio_data))
            
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection error to megaservice: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
            except requests.exceptions.Timeout as e:
                error_msg = f"Timeout connecting to megaservice: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg, exc_info=True)
                st.error(error_msg)

# Display chat history if it exists
if "chat_history" in st.session_state and st.session_state.chat_history:
    st.subheader("Chat History")
    for i, (question, answer, audio) in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"Q: {question[:50]}..." if len(question) > 50 else f"Q: {question}", expanded=(i==0)):
            st.write("**Question:**")
            st.write(question)
            st.write("**Answer:**")
            st.write(answer)
            if audio:
                st.audio(audio)
