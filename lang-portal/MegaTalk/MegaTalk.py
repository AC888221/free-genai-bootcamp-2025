import streamlit as st
from pathlib import Path
from backend.chat_service import (
    get_chat_response,
    create_or_get_session  # Add this import
)
from backend.config import (
    logger, 
    POLLY_DEFAULTS,
    TRANSCRIBE_DEFAULTS,  # Add this import
    BEDROCK_SYSTEM_MESSAGE  # Add this import
)
from backend.prompts import (
    get_hsk_prompt,
    get_topic_prompt,
    get_formality_prompt,
    get_goal_prompt,
    TOPICS,
    FORMALITY_LEVELS
)
from backend.db_utils import get_all_sessions, get_session_messages, delete_session
from typing import Optional, Dict, Tuple
import uuid
import time
from backend.transcribe_client import transcribe_client  # Import the client directly
import io
from audio_recorder_streamlit import audio_recorder
from pydub import AudioSegment

# Configure the page layout
st.set_page_config(
    page_title="MegaTalk",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "formality" not in st.session_state:
        st.session_state.formality = "Neutral"
    if "hsk_level" not in st.session_state:
        st.session_state.hsk_level = "HSK 1 (Beginner)"
    if "selected_topics" not in st.session_state:
        st.session_state.selected_topics = ["General Conversation"]
    if "learning_goal" not in st.session_state:
        st.session_state.learning_goal = ""
    if "generate_audio" not in st.session_state:
        st.session_state.generate_audio = True
    if "enable_voice_input" not in st.session_state:
        st.session_state.enable_voice_input = True

def display_chat_message(message_data):
    """Display a chat message with optional audio."""
    with st.chat_message(message_data["role"]):
        # For user messages, only display the actual message part
        if message_data["role"] == "user":
            # Extract just the user's message if it contains the full prompt
            content = message_data["content"]
            if "User: " in content:
                content = content.split("User: ")[-1]
            st.markdown(content)
        else:
            st.markdown(message_data["content"])
            
        if "audio" in message_data and message_data["audio"] is not None:
            # Handle both audio bytes and file paths
            audio_data = message_data["audio"]
            if isinstance(audio_data, str):  # It's a file path
                try:
                    with open(audio_data, 'rb') as f:
                        audio_data = f.read()
                except Exception as e:
                    logger.error(f"Error reading audio file {audio_data}: {e}")
                    return
            
            # Convert audio data to base64 for HTML audio element
            import base64
            audio_base64 = base64.b64encode(audio_data).decode()
            audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            # Keep the regular audio player as fallback
            st.audio(audio_data, format="audio/mp3")

def display_chat_history_selector():
    """Display a dropdown to select previous chat sessions."""
    sessions = get_all_sessions()
    if sessions:
        session_options = ["Select a session..."] + [
            f"Session {idx + 1} - {session['created_at'][:16]}"
            for idx, session in enumerate(sessions)
        ]
        selected_session = st.selectbox(
            "Previous chats",
            session_options,
            index=0
        )
        
        col1, col2 = st.columns(2)
        
        # Add buttons but disable them if no session is selected
        is_session_selected = selected_session != "Select a session..."
        
        # Add a button to load the selected session
        if col1.button("Load Chat", disabled=not is_session_selected):
            if is_session_selected:
                session_idx = int(selected_session.split(" - ")[0].split(" ")[1]) - 1
                session_id = sessions[session_idx]['session_id']
                messages = get_session_messages(session_id)
                st.session_state.messages = [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "audio": msg["audio_path"] if msg["audio_path"] else None
                    }
                    for msg in messages
                ]
                st.session_state.current_session_id = session_id
                st.rerun()
        
        # Add a button to delete the selected session
        if col2.button("Delete Chat", disabled=not is_session_selected):
            if is_session_selected:
                session_idx = int(selected_session.split(" - ")[0].split(" ")[1]) - 1
                session_id = sessions[session_idx]['session_id']
                if delete_session(session_id):
                    if session_id == st.session_state.get("current_session_id"):
                        st.session_state.messages = []
                        st.session_state.current_session_id = None
                    st.success("Chat deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete chat.")
    else:
        st.info("No saved sessions yet.")

def process_audio_input(audio_bytes: bytes) -> Optional[str]:
    """Process audio input using transcribe client"""
    try:
        with st.spinner("Transcribing..."):
            transcribed_text = transcribe_client.transcribe_audio(
                audio_bytes,
                language_code=TRANSCRIBE_DEFAULTS["language_code"]
            )
            if transcribed_text:
                logger.info("Successfully transcribed audio input")
                return transcribed_text
            else:
                logger.error("Failed to transcribe audio input")
                st.error("Failed to transcribe audio")
                return None
    except Exception as e:
        logger.error(f"Error in audio transcription: {str(e)}")
        st.error(f"Error processing audio: {str(e)}")
        return None

def convert_audio_for_transcribe(audio_bytes: bytes) -> bytes:
    """Convert audio to format required by AWS Transcribe"""
    try:
        # Load audio from bytes
        audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Convert sample rate if needed
        if audio.frame_rate != TRANSCRIBE_DEFAULTS["sample_rate"]:
            audio = audio.set_frame_rate(TRANSCRIBE_DEFAULTS["sample_rate"])
        
        # Export to bytes
        output = io.BytesIO()
        audio.export(output, format='wav')
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return audio_bytes  # Return original on error

def main():
    # Add custom CSS to adjust the layout
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-left: 5rem;
            padding-right: 5rem;
            padding-bottom: 6rem;
        }
        
        .stChat {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem 5rem;
            z-index: 1000;
            border-top: 1px solid #ddd;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 MegaTalk - Your AI Language Buddy")
    
    initialize_session_state()
    
    # Sidebar controls
    with st.sidebar:
        tab1, tab2 = st.tabs(["Settings", "Chat Sessions"])
        
        with tab1:
            st.header("Settings")
            
            # Language Level
            st.subheader("Language Level")
            st.session_state.hsk_level = st.selectbox(
                "HSK Level",
                ["HSK 1 (Beginner)", "HSK 2 (Elementary)", 
                 "HSK 3 (Intermediate)", "HSK 4 (Advanced Intermediate)",
                 "HSK 5 (Advanced)", "HSK 6 (Mastery)"],
                key="hsk_level_select"
            )
            
            # Topics
            st.subheader("Conversation Topics")
            selected_topics = st.multiselect(
                "Select preferred topics",
                TOPICS,
                default=["General Conversation"]
            )
            
            # Learning Goals
            st.subheader("Learning Goals")
            learning_goal = st.text_area(
                "What would you like to focus on?",
                placeholder="Example: Practice using past tense, Learn food vocabulary, Practice making comparisons...",
                help="Enter specific aspects of Putonghua you want to practice in this conversation."
            )
            
            # Formality
            st.subheader("Conversation Style")
            formality = st.radio(
                "Formality Level",
                options=["Casual", "Neutral", "Formal", "Highly Formal"],
                index=1,
                key="formality_select"
            )
            
            # Audio Settings
            st.subheader("Audio Settings")
            st.session_state.generate_audio = st.checkbox(
                "Generate audio response", 
                value=st.session_state.generate_audio
            )
            st.session_state.enable_voice_input = st.checkbox(
                "Enable voice input", 
                value=st.session_state.enable_voice_input,
                help="Allow voice input using microphone"
            )
        
        with tab2:
            st.header("Chat Sessions")
            # New Chat button at the top
            if st.button("New Chat", type="primary"):
                st.session_state.messages = []
                st.session_state.current_session_id = None
                st.rerun()
            
            st.divider()
            display_chat_history_selector()
            
            # Export chat option
            if st.session_state.messages:  # Only show if there are messages
                st.divider()
                if st.button("Export Current Chat"):
                    chat_text = "\n\n".join([
                        f"{msg['role'].title()}: {msg['content']}"
                        for msg in st.session_state.messages
                    ])
                    st.download_button(
                        label="Download Chat",
                        data=chat_text,
                        file_name="chat_export.txt",
                        mime="text/plain"
                    )
    
    # Chat display
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message)
    
    # Chat input section
    col1, col2 = st.columns([8, 2])
    with col1:
        pass
    with col2:
        if st.session_state.enable_voice_input:
            # Upload method selection
            upload_method = st.radio(
                "Choose upload method:",
                ["Microphone", "File Upload", "WSL Path", "URL"],
                key="voice_upload_method",
                label_visibility="collapsed"
            )

            if upload_method == "Microphone":
                # Add a key to the audio_recorder to prevent state conflicts
                current_audio = audio_recorder(key="mic_recorder")
                
                # Only process if we have new audio and it's different from the last processed audio
                if current_audio and hash(current_audio) != st.session_state.get('last_audio_hash'):
                    # Store hash of current audio to prevent reprocessing
                    st.session_state.last_audio_hash = hash(current_audio)
                    
                    # Log original audio info
                    logger.info(f"Original recorded audio size: {len(current_audio)} bytes")
                    try:
                        import wave
                        with io.BytesIO(current_audio) as bio:
                            bio.write(current_audio)
                            bio.seek(0)
                            with wave.open(bio, 'rb') as wav:
                                channels = wav.getnchannels()
                                sample_width = wav.getsampwidth()
                                frame_rate = wav.getframerate()
                                frames = wav.getnframes()
                                duration = frames / frame_rate
                                
                                logger.info("\nOriginal Audio Information:")
                                logger.info(f"Channels: {channels}")
                                logger.info(f"Sample Width: {sample_width * 8}bit")
                                logger.info(f"Frame Rate: {frame_rate}Hz")
                                logger.info(f"Frames: {frames}")
                                logger.info(f"Duration: {duration:.2f} seconds")
                                
                    except Exception as e:
                        logger.error(f"Could not read original audio properties: {e}")
                    
                    # Convert audio to required format
                    converted_audio = convert_audio_for_transcribe(current_audio)
                    
                    # Process the audio
                    transcribed_text = process_audio_input(converted_audio)
                    if transcribed_text:
                        # Log the actual transcribed text
                        logger.info(f"Transcribed text: '{transcribed_text}'")
                        st.session_state.transcribed_text = transcribed_text
                        # Don't call st.rerun() here - let Streamlit handle the update
    
            elif upload_method == "File Upload":
                uploaded_file = st.file_uploader(
                    "Upload audio file",
                    type=["wav", "mp3"],
                    key="voice_file",
                    label_visibility="collapsed"
                )
                if uploaded_file:
                    audio_bytes = uploaded_file.read()
                    transcribed_text = process_audio_input(audio_bytes)
                    if transcribed_text:
                        st.session_state.transcribed_text = transcribed_text
                        st.rerun()

            elif upload_method == "WSL Path":
                file_path = st.text_input(
                    "Enter file path:",
                    key="voice_path",
                    help="Example: /mnt/c/Users/YourName/audio.wav",
                    label_visibility="collapsed",
                    placeholder="/path/to/audio.wav"
                )
                if st.button("Transcribe", key="path_transcribe"):
                    try:
                        with open(file_path, 'rb') as f:
                            audio_bytes = f.read()
                        with st.spinner("Transcribing..."):
                            transcribed_text = process_audio_input(audio_bytes)
                            if transcribed_text:
                                st.session_state.transcribed_text = transcribed_text
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")

            else:  # URL option
                url = st.text_input(
                    "Enter audio URL:",
                    key="voice_url",
                    label_visibility="collapsed",
                    placeholder="https://example.com/audio.wav"
                )
                if st.button("Transcribe", key="url_transcribe"):
                    try:
                        import requests
                        with st.spinner("Downloading and transcribing..."):
                            response = requests.get(url)
                            if response.status_code == 200:
                                audio_bytes = response.content
                                transcribed_text = process_audio_input(audio_bytes)
                                if transcribed_text:
                                    st.session_state.transcribed_text = transcribed_text
                                    st.rerun()
                            else:
                                st.error("Failed to download audio file")
                    except Exception as e:
                        st.error(f"Error downloading file: {str(e)}")
    
    # Single chat input at the bottom
    if "transcribed_text" in st.session_state:
        # Can't set value directly, so we'll use the transcribed text differently
        prompt = st.chat_input("What's on your mind?", key="chat_input")
        if not prompt:  # If no new input, use the transcribed text
            prompt = st.session_state.transcribed_text
            del st.session_state.transcribed_text  # Clean up
    else:
        prompt = st.chat_input("What's on your mind?", key="chat_input")

    if prompt:
        # Create new session if none exists
        if not st.session_state.get("current_session_id"):
            st.session_state.current_session_id = create_or_get_session()
            
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        display_chat_message(user_message)
        
        # Construct the prompt
        full_prompt = f"""{BEDROCK_SYSTEM_MESSAGE}

Language Level:
{get_hsk_prompt(st.session_state.hsk_level)}

Style and Topics:
{get_formality_prompt(formality)}
{get_topic_prompt(selected_topics)}

{get_goal_prompt(learning_goal)}

User: {prompt}"""
        
        # Configure TTS settings with default voice
        config_params = {
            "generate_audio": st.session_state.generate_audio,
            "voice": "Zhiyu"  # Using default voice directly
        }
        
        # Get response with session ID
        response_text, audio_data, error, details = get_chat_response(
            full_prompt, 
            session_id=st.session_state.current_session_id,
            config_params=config_params
        )
        
        if error:
            st.error(f"Error: {error}")
            return
        
        # Display response
        assistant_message = {
            "role": "assistant",
            "content": response_text
        }
        if audio_data:
            assistant_message["audio"] = audio_data
        
        st.session_state.messages.append(assistant_message)
        display_chat_message(assistant_message)

if __name__ == "__main__":
    main()