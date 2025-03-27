import streamlit as st
from pathlib import Path
from backend.chat_service import (
    get_chat_response,
    create_or_get_session  # Add this import
)
from backend.config import (
    logger, 
    POLLY_DEFAULTS,
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
        # For user messages, only display the actual message part
        if message_data["role"] == "user":
            # Extract just the user's message if it contains the full prompt
            content = message_data["content"]
            if "User: " in content:
                content = content.split("User: ")[-1]
            st.markdown(content)
        else:
            st.markdown(message_data["content"])
            
        if "audio" in message_data:
            st.audio(message_data["audio"], format="audio/mp3")

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
            generate_audio = st.checkbox("Generate audio response", value=True)
        
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
    
    # Chat input
    if prompt := st.chat_input("What's on your mind?", key="chat_input"):
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
            "generate_audio": generate_audio,
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