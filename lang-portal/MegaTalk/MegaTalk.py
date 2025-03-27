import streamlit as st
from pathlib import Path
from backend.chat_service import get_chat_response
from backend.config import (
    logger, 
    POLLY_DEFAULTS  # Import the defaults
)
from backend.prompts import (
    get_hsk_prompt,
    get_system_prompt,
    get_topic_prompt,
    get_formality_prompt,
    get_goal_prompt,
    TOPICS,
    FORMALITY_LEVELS
)

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

def display_chat_message(message_data):
    """Display a chat message with optional audio."""
    with st.chat_message(message_data["role"]):
        st.markdown(message_data["content"])
        if "audio" in message_data:
            st.audio(message_data["audio"], format="audio/mp3")

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
        generate_audio = st.checkbox("Generate audio response", value=True)
        
        if generate_audio:
            voice_id = st.selectbox(
                "Voice",
                ["Zhiyu"],  # Could expand with more Chinese voices if available
                index=0
            )
    
    # Chat display
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message)
    
    # Chat input
    if prompt := st.chat_input("What's on your mind?", key="chat_input"):
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        display_chat_message(user_message)
        
        # Construct the prompt
        full_prompt = f"""{get_system_prompt()}

Language Level:
{get_hsk_prompt(st.session_state.hsk_level)}

Style and Topics:
{get_formality_prompt(formality)}
{get_topic_prompt(selected_topics)}

{get_goal_prompt(learning_goal)}

User: {prompt}"""
        
        # Configure TTS settings
        config_params = {
            "generate_audio": generate_audio,
            "voice": voice_id if generate_audio else None
        }
        
        # Get response
        response_text, audio_data, error, details = get_chat_response(full_prompt, config_params)
        
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