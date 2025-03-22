import streamlit as st
import time
import base64
from pathlib import Path
from backend.chat_service import get_chat_response
from backend.config import logger
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
            padding-bottom: 6rem;  /* Add padding at bottom for chat input */
        }
        
        /* Style for sticking chat input to bottom */
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
    
    # Initialize session state
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
        
        # Add debug logging for formality
        logger.info(f"Selected formality: {formality}")
        formality_instructions = get_formality_prompt(formality)
        logger.info(f"Raw formality instructions: {formality_instructions}")
        
        # Audio
        st.subheader("Audio Settings")
        generate_audio = st.checkbox("Generate audio response", value=True)
    
    # Create main chat container
    chat_container = st.container()
    
    # Display chat history in the container
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message)
    
    # Chat input at bottom
    if prompt := st.chat_input("What's on your mind?", key="chat_input"):
        # Add user message to history first
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        display_chat_message(user_message)
        
        # Use session state values
        logger.info("Current Settings:")
        logger.info(f"HSK Level: {st.session_state.hsk_level}")
        logger.info(f"Selected Topics: {selected_topics}")
        logger.info(f"Learning Goal: {learning_goal}")
        logger.info(f"Formality Level: {formality}")  # Use local variable instead of session state
        logger.info(f"Generate Audio: {generate_audio}")
        
        # Construct prompts using the local formality variable
        system_prompt = get_system_prompt()
        hsk_instructions = get_hsk_prompt(st.session_state.hsk_level)
        topic_instructions = get_topic_prompt(selected_topics)
        formality_instructions = get_formality_prompt(formality)  # Use local variable
        goal_instructions = get_goal_prompt(learning_goal)
        
        # Add debug logging for formality prompt
        logger.info(f"Using formality level: {formality}")
        logger.info(f"Formality instructions generated: {formality_instructions[:100]}...")
        
        # Log the constructed prompts
        logger.info("Constructed Prompts:")
        logger.info(f"System Prompt: {system_prompt[:100]}...")
        logger.info(f"HSK Instructions: {hsk_instructions[:100]}...")
        logger.info(f"Topic Instructions: {topic_instructions[:100]}...")
        logger.info(f"Formality Instructions: {formality_instructions[:100]}...")
        logger.info(f"Goal Instructions: {goal_instructions[:100]}...")
        
        full_prompt = f"""{system_prompt}

Language Level:
{hsk_instructions}

Style and Topics:
{formality_instructions}
{topic_instructions}

{goal_instructions}

User: {prompt}"""
        
        # Log the full prompt length
        logger.info(f"Full Prompt Length: {len(full_prompt)} characters")
        
        # Get AI response
        config_params = {
            "generate_audio": generate_audio,
            "voice": "default"
        }
        
        logger.info(f"Sending request: {prompt[:20]}...")
        response_text, audio_data, error, details = get_chat_response(full_prompt, config_params)
        
        if error:
            logger.error(f"Error received: {error}")
            st.error(f"Error: {error}")
            return
        
        # Create and display AI response
        assistant_message = {
            "role": "assistant",
            "content": response_text
        }
        if audio_data:
            assistant_message["audio"] = audio_data
        
        st.session_state.messages.append(assistant_message)
        display_chat_message(assistant_message)
        
        # Log response details
        logger.info(f"Response Details: {details}")

if __name__ == "__main__":
    main()