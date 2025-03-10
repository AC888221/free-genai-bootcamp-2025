import streamlit as st
import requests
import base64
import io
from typing import Optional
import os

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

if st.button("Submit"):
    if not user_input.strip():
        st.error("Please enter a message")
    else:
        with st.spinner("Processing..."):
            # Call the megaservice API
            try:
                response = requests.post(
                    f"{MEGASERVICE_URL}/v1/megaservice",
                    json={
                        "text": user_input,
                        "model": model,
                        "voice": voice,
                        "generate_audio": generate_audio,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code != 200:
                    st.error(f"Error: {response.status_code} - {response.text}")
                else:
                    data = response.json()
                    
                    # Display text response
                    st.subheader("Text Response")
                    st.write(data["text_response"])
                    
                    # Display audio if available
                    if generate_audio and data.get("audio_data") and data.get("audio_format"):
                        st.subheader("Audio Response")
                        audio_bytes = base64.b64decode(data["audio_data"])
                        st.audio(audio_bytes, format=f"audio/{data['audio_format']}")
                        
                        # Add download button for audio
                        st.download_button(
                            label="Download Audio",
                            data=audio_bytes,
                            file_name=f"response.{data['audio_format']}",
                            mime=f"audio/{data['audio_format']}"
                        )
                    
                    # Add to chat history
                    audio_bytes = base64.b64decode(data["audio_data"]) if generate_audio and data.get("audio_data") else None
                    if "chat_history" not in st.session_state:
                        st.session_state.chat_history = []
                    st.session_state.chat_history.append((user_input, data["text_response"], audio_bytes))
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

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
