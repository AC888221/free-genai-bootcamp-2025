import streamlit as st
import time
import base64
from pathlib import Path

from backend.config import (
    logger,
    BASE_TIMEOUT,
    TIMEOUT_PER_CHAR
)
from backend.conversation import call_megaservice

# App title and description
st.title("MegaTalk - Chinese Language Practice")
st.write("Practice Chinese conversation with an AI language partner!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("Starting MegaTalk application")

# Sidebar configuration
with st.sidebar:
    st.header("Settings")
    generate_audio = st.checkbox("Generate Audio", value=False)
    
    if generate_audio:
        voice = st.selectbox(
            "Voice",
            ["default", "female", "male"],
            index=0
        )
    else:
        voice = "default"

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/wav")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        config_params = {
            "generate_audio": generate_audio,
            "voice": voice
        }
        
        logger.info(f"Sending request: {prompt}...")
        response_text, audio_data, error, details = call_megaservice(prompt, config_params)
        
        if error:
            message_placeholder.error(f"Error: {error}")
        else:
            message_placeholder.write(response_text)
            if audio_data:
                st.audio(audio_data, format="audio/wav")
            
            # Add assistant response to chat history
            message_data = {
                "role": "assistant",
                "content": response_text
            }
            if audio_data:
                message_data["audio"] = audio_data
            st.session_state.messages.append(message_data)